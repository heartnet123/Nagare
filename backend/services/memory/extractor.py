"""Memory extractor — background LLM extraction of durable facts from chat.

Port of Odysseus' ``services/memory/memory_extractor.py``.  After each agent
conversation turn, this module can be called to send the last few messages to
the LLM, which extracts memorable personal facts and stores them in both the
JSON-backed ``MemoryManager`` and the ``MemoryVectorStore``.

Also includes a periodic audit pipeline that deduplicates, consolidates, and
removes junk memories.

Key differences from the Odysseus original:
- No ``<think>``‑tag stripping (can be added per-model).
- Simpler LLM client adapter — takes a callable instead of coupling to
  Odysseus' ``llm_core``.
- Uses Nagare's ``MemoryManager`` / ``MemoryVectorStore`` directly.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXTRACT_SYSTEM_PROMPT = (
    "You are a memory extraction assistant. Analyze the conversation and extract ONLY "
    "durable personal facts about the user that would be useful across many future conversations.\n\n"
    "Good examples: name, job title, city, family members, long-term projects, strong preferences.\n"
    "Bad examples: what they asked about today, temporary moods, generic statements, "
    "things the assistant said, one-off tasks, opinions on the current topic.\n\n"
    "Rules:\n"
    "- MAX 2 facts per conversation — only the most important\n"
    "- Only extract facts the USER stated or clearly implied\n"
    "- Each fact must be a single short sentence (under 15 words)\n"
    "- If a fact is similar to something likely already known, skip it\n"
    "- If nothing durable was revealed, return []\n\n"
    "Return a JSON array of objects with 'text' and 'category' fields.\n"
    "Categories: 'identity', 'preference', 'fact', 'contact', 'project', 'goal'\n\n"
    "Return ONLY valid JSON, no markdown fences."
)

AUDIT_SYSTEM_PROMPT = (
    "You are a memory database curator. Be CONSERVATIVE: remove only TRUE "
    "duplicates and clearly useless entries. Every distinct fact must survive. "
    "When in doubt, KEEP the entry. Return the cleaned list.\n\n"
    "Rules:\n"
    "1. MERGE only entries that state the SAME fact in different words. If you "
    "are not sure two entries are the same fact, KEEP BOTH.\n"
    "   Merge: 'User's name is Sam' + 'The user is called Sam' -> one.\n"
    "   Do NOT merge related-but-distinct facts: 'Likes Python' and 'Uses "
    "Python at work' are DIFFERENT — keep both.\n"
    "2. REMOVE only entries that are genuinely worthless: about what the AI did "
    "(not the user), empty, or meaningless. Do NOT drop a real fact just "
    "because it seems minor or niche.\n"
    "3. Keep the original wording. Only lightly trim obvious redundancy — do "
    "NOT aggressively rewrite or shorten.\n"
    "4. Preserve the 'id' of the entry you keep when merging.\n"
    "5. Never invent facts. When unsure, KEEP.\n\n"
    "Return a JSON array of objects with fields: id, text, category.\n"
    "Return ONLY valid JSON, no markdown fences."
)

CONTEXT_WINDOW = 6  # last N messages sent to the LLM
AUDIT_INTERVAL = 5  # run audit every N new memories

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _message_text(message: Any) -> str:
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return " ".join(p for p in parts if p).strip()
    return ""


def _message_role(message: Any) -> str:
    role = getattr(message, "role", None)
    if role is None and isinstance(message, dict):
        role = message.get("role")
    return str(role or "").lower()


def _clean_value(value: str, max_len: int = 80) -> str:
    value = re.sub(r"\s+", " ", value or "").strip(" .,!?:;\"'`\u201c\u201d\u2018\u2019")
    value = re.sub(r"^(?:the|a|an)\s+", "", value, flags=re.I)
    if not value or len(value) > max_len:
        return ""
    if re.search(r"https?://|@|[{}<>]", value):
        return ""
    return value


def _fallback_candidates(messages: List[Any]) -> List[Dict]:
    """Extract obvious durable facts without an LLM call.

    Covers the same patterns as Odysseus' ``_fallback_memory_candidates``:
    name, location, preferences, goals.
    """
    candidates: List[Dict] = []
    seen: set = set()

    def add(text: str, category: str) -> None:
        text = _clean_value(text, 120)
        if not text:
            return
        key = text.lower()
        if key in seen:
            return
        seen.add(key)
        candidates.append({"text": text, "category": category})

    for msg in messages:
        if _message_role(msg) != "user":
            continue
        text = _message_text(msg)
        if not text:
            continue

        m = re.search(r"\bmy name is\s+([A-Za-z][A-Za-z0-9 .'\-]{1,50})\b", text, re.I)
        if m:
            name = _clean_value(m.group(1), 50)
            if name:
                add(f"User's name is {name}.", "identity")

        m = re.search(r"\bcall me\s+([A-Za-z][A-Za-z0-9 .'\-]{1,50})\b", text, re.I)
        if m:
            name = _clean_value(m.group(1), 50)
            if name:
                add(f"User wants to be called {name}.", "identity")

        m = re.search(r"\bi (?:live in|am from|'m from)\s+([^.!?\n]{2,80})", text, re.I)
        if m:
            place = _clean_value(m.group(1), 80)
            if place:
                add(f"User lives in {place}.", "identity")

        m = re.search(
            r"\bi (prefer|like|love|hate|do not like|don't like)\s+([^.!?\n]{4,100})",
            text, re.I,
        )
        if m:
            pref = _clean_value(m.group(2), 100)
            if pref:
                verb = m.group(1).lower()
                if verb in ("hate", "do not like", "don't like"):
                    add(f"User dislikes {pref}.", "preference")
                else:
                    add(f"User prefers {pref}.", "preference")

        m = re.search(
            r"\bi (?:(?:want|would like|plan|hope) to|wanna) "
            r"(?:go|travel|move|visit) to\s+([^.!?\n]{2,80})",
            text, re.I,
        )
        if m:
            dest = _clean_value(m.group(1), 80)
            if dest:
                add(f"User wants to visit {dest}.", "goal")

    return candidates[:2]


def _is_text_duplicate(new_text: str, existing: List[Dict], threshold: float = 0.6) -> bool:
    """Jaccard-overlap dedup against existing entries."""
    new_tokens = set(new_text.lower().split())
    if not new_tokens:
        return False
    for entry in existing:
        old_tokens = set(entry.get("text", "").lower().split())
        if not old_tokens:
            continue
        inter = new_tokens & old_tokens
        union = new_tokens | old_tokens
        if len(inter) / len(union) >= threshold:
            return True
    return False


def _parse_extraction_json(raw: str) -> List:
    """Parse the LLM's reply into a list of facts, tolerating fences and
    trailing commentary."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    start = text.find("[")
    end = text.rfind("]")
    if 0 <= start < end:
        text = text[start : end + 1]
    try:
        facts = json.loads(text)
    except (json.JSONDecodeError, Exception):
        logger.debug("Extraction returned non-JSON: %r", (raw or "")[:120])
        return []
    return facts if isinstance(facts, list) else []


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------


async def extract_and_store(
    memory_manager,
    memory_vector,
    context_messages: List[Any],
    llm_call: Callable,
    *,
    owner: Optional[str] = None,
    session_id: Optional[str] = None,
) -> int:
    """Extract facts from conversation and store them.

    Parameters
    ----------
    memory_manager : MemoryManager
        The JSON-backed memory store.
    memory_vector : MemoryVectorStore or None
        Optional vector store for semantic search.
    context_messages : list
        Recent chat messages (each has ``role`` and ``content``).
    llm_call : async callable
        ``await llm_call(messages) -> str``.  Called with the extraction
        prompt; should return the raw LLM response text.
    owner : str, optional
        Owner to stamp on extracted memories.
    session_id : str, optional
        Session association.

    Returns
    -------
    int
        Number of new memories stored.
    """
    # Need at least 2 messages (user + assistant) to extract
    if len(context_messages) < 2:
        return 0

    recent = context_messages[-CONTEXT_WINDOW:]

    # Strip multimodal blocks — keep only text
    stripped = []
    for msg in recent:
        role = _message_role(msg)
        content = msg.get("content", "") if isinstance(msg, dict) else ""
        if isinstance(content, list):
            text_only = [
                b for b in content
                if isinstance(b, dict) and b.get("type") == "text"
            ]
            if not text_only and content:
                continue
            content = text_only
        stripped.append({"role": role, "content": content})

    if not stripped:
        return 0

    fallback_facts = _fallback_candidates(stripped)

    # Flatten into a single transcript block for the LLM
    def _flatten(m):
        c = m.get("content", "")
        if isinstance(c, list):
            c = " ".join(
                b.get("text", "") for b in c
                if isinstance(b, dict) and b.get("type") == "text"
            )
        return f"{m.get('role', '?')}: {c}"

    transcript = "\n\n".join(_flatten(m) for m in stripped)
    extraction_messages = [
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Conversation to analyze:\n\n" + transcript
                + "\n\nReturn the JSON array of durable facts now (or [] if none)."
            ),
        },
    ]

    facts: List = []
    try:
        raw = await llm_call(extraction_messages)
        facts = _parse_extraction_json(raw)
    except Exception as exc:
        logger.warning("LLM extraction failed; using fallback: %s", exc)

    if not isinstance(facts, list):
        facts = []

    if fallback_facts:
        facts = list(facts) + fallback_facts

    if not facts:
        logger.info("Memory extraction: 0 candidates")
        return 0

    existing = memory_manager.load_all()
    added = 0

    for fact in facts:
        if isinstance(fact, str):
            fact_text = fact
            category = "fact"
        elif isinstance(fact, dict):
            fact_text = fact.get("text", "").strip()
            category = fact.get("category", "fact")
        else:
            continue

        if not fact_text or len(fact_text) < 5:
            continue

        # Vector dedup
        if memory_vector and memory_vector.healthy:
            try:
                existing_id = memory_vector.find_similar(fact_text, threshold=0.72)
            except Exception:
                existing_id = None
            if existing_id:
                _match = next(
                    (e for e in existing if e.get("id") == existing_id), None
                )
                if _match is not None and (
                    _match.get("owner") == owner or _match.get("owner") is None
                ):
                    logger.debug("Dedup (vector): %r matched %s", fact_text[:50], existing_id)
                    continue

        # Text dedup
        user_existing = (
            [e for e in existing if e.get("owner") == owner or e.get("owner") is None]
            if owner else existing
        )
        if memory_manager.find_duplicates(fact_text, user_existing):
            continue
        if _is_text_duplicate(fact_text, user_existing):
            logger.debug("Dedup (fuzzy): %r too similar", fact_text[:50])
            continue

        entry = memory_manager.add_entry(
            fact_text,
            source="auto",
            category=category,
            owner=owner,
            session_id=session_id,
        )
        if category == "identity":
            entry["pinned"] = True
        existing.append(entry)

        if memory_vector and memory_vector.healthy:
            try:
                memory_vector.add(entry["id"], fact_text)
            except Exception as exc:
                logger.warning("Vector add failed for %s: %s", entry["id"], exc)

        added += 1

    if added > 0:
        memory_manager.save(existing)
        logger.info("Auto-extracted %d memories", added)

    return added


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


async def audit_memories(
    memory_manager,
    memory_vector,
    llm_call: Callable,
    *,
    owner: Optional[str] = None,
) -> Dict:
    """Send all memories to the LLM for dedup/consolidation.

    Returns ``{"before": int, "after": int}`` or
    ``{"error": str}`` on failure.
    """
    existing = memory_manager.load(owner=owner)
    if not existing:
        return {"before": 0, "after": 0}

    before = len(existing)

    payload = [
        {"id": m["id"], "text": m["text"], "category": m.get("category", "fact")}
        for m in existing
    ]

    audit_messages = [
        {"role": "system", "content": AUDIT_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        raw = await llm_call(audit_messages)
    except Exception as exc:
        logger.error("Audit LLM call failed: %s", exc)
        return {"before": before, "after": before, "error": str(exc)}

    text = (raw or "").strip()
    # Strip markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    start = text.find("[")
    end = text.rfind("]")
    if 0 <= start < end:
        text = text[start : end + 1]

    try:
        cleaned = json.loads(text)
    except json.JSONDecodeError:
        logger.error("Audit returned non-JSON: %r", text[:300])
        return {"before": before, "after": before, "error": "bad_json"}

    if not isinstance(cleaned, list):
        return {"before": before, "after": before, "error": "bad_json"}

    originals = {m["id"]: m for m in existing}
    final = []
    for item in cleaned:
        if not isinstance(item, dict):
            continue
        mid = item.get("id", "")
        new_text = item.get("text", "").strip()
        if not new_text:
            continue
        if mid in originals:
            entry = originals[mid].copy()
            entry["text"] = new_text
            if item.get("category"):
                entry["category"] = item["category"]
            final.append(entry)
        else:
            logger.debug("Audit: unknown id %s, skipping", mid)

    after = len(final)

    # Safety: don't drop >50% in one pass
    if before >= 8 and after < before * 0.5:
        logger.warning(
            "Audit would cut %d -> %d (>50%%), refusing as unsafe",
            before, after,
        )
        return {"before": before, "after": before, "error": "unsafe_removal"}

    if owner:
        all_entries = memory_manager.load_all()
        audited_ids = {e["id"] for e in final}
        other = [
            e for e in all_entries
            if e.get("owner") != owner or e.get("owner") is None
        ]
        saved = final + other
    else:
        saved = final

    memory_manager.save(saved)
    logger.info("Audit complete: %d -> %d entries", before, after)

    if memory_vector and memory_vector.healthy:
        memory_vector.rebuild(saved)

    return {"before": before, "after": after}
