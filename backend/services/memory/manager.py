"""Memory manager — JSON-backed persistent memory store.

Port of Odysseus' ``src/memory.py`` — modified to fit Nagare's existing
``services/agent/memory.py`` layout.  Adds keyword, fuzzy (Jaccard), and
semantic-category scoring on top of the simple keyword store Nagare already has.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token / similarity helpers (pure, no state)
# ---------------------------------------------------------------------------


def tokenize(text: str) -> List[str]:
    """Split on whitespace and strip common punctuation."""
    return [word.strip('.,!?";:()[]') for word in text.split() if word.strip()]


def get_text_similarity(text1: str, text2: str) -> float:
    """Jaccard similarity between two strings."""
    if not text1 or not text2:
        return 0.0
    tokens1 = set(tokenize(text1.lower()))
    tokens2 = set(tokenize(text2.lower()))
    if not tokens1 and not tokens2:
        return 1.0
    if not tokens1 or not tokens2:
        return 0.0
    return len(tokens1 & tokens2) / len(tokens1 | tokens2)


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------------------
# MemoryManager
# ---------------------------------------------------------------------------


class MemoryManager:
    """Manage durable memory entries backed by a JSON file.

    Each entry has the shape::

        {
            "id":         str,       # uuid4
            "text":       str,       # the fact
            "timestamp":  int,       # unix epoch
            "source":     str,       # user | auto | learned
            "category":   str,       # identity | preference | fact | contact | project | goal
            "owner":      str | None,
            "session_id": str | None,
            "pinned":     bool,      # true for identity facts
            "uses":       int,       # retrieval count
        }
    """

    def __init__(self, path: str | Path):
        self.memory_file = Path(path)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file()

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def _ensure_file(self) -> None:
        if not self.memory_file.exists():
            self.memory_file.write_text("[]", encoding="utf-8")

    def load_all(self) -> List[Dict[str, Any]]:
        """Return every memory entry (unfiltered)."""
        if not self.memory_file.exists():
            return []
        try:
            data = json.loads(self.memory_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return self._validate_entries(data)
        except (json.JSONDecodeError, PermissionError, OSError) as exc:
            logger.error("Failed to load %s: %s", self.memory_file, exc)
            return []
        return []

    def load(self, owner: str | None = None) -> List[Dict[str, Any]]:
        """Return memories, optionally filtered by *owner*."""
        entries = self.load_all()
        if owner is None:
            return entries
        return [e for e in entries if e.get("owner") == owner]

    def save(self, entries: List[Dict[str, Any]]) -> None:
        """Atomically write the full list to disk."""
        for entry in entries:
            if "id" not in entry:
                entry["id"] = str(uuid.uuid4())
            if "timestamp" not in entry:
                entry["timestamp"] = int(time.time())
            if "source" not in entry:
                entry["source"] = "user"
            if "category" not in entry:
                entry["category"] = "fact"

        tmp = str(self.memory_file) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(self.memory_file))

    def claim_ownerless(self, owner: str) -> int:
        """Assign all ownerless entries to *owner*. Returns count changed."""
        entries = self.load_all()
        changed = 0
        for entry in entries:
            if not entry.get("owner"):
                entry["owner"] = owner
                changed += 1
        if changed:
            self.save(entries)
            logger.info("Claimed %d ownerless memories for %s", changed, owner)
        return changed

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add_entry(
        self,
        text: str,
        source: str = "user",
        category: str = "fact",
        owner: str | None = None,
        session_id: str | None = None,
        pinned: bool = False,
    ) -> Dict[str, Any]:
        """Create a new entry dict (does **not** persist)."""
        text = text.strip()
        if not text:
            raise ValueError("Memory text cannot be empty")
        return {
            "id": str(uuid.uuid4()),
            "text": text,
            "timestamp": int(time.time()),
            "source": source,
            "category": category,
            "owner": owner,
            "session_id": session_id,
            "pinned": pinned,
            "uses": 0,
        }

    def increment_uses(self, ids: List[str]) -> None:
        """Bump the uses counter for each memory id."""
        if not ids:
            return
        id_set = set(ids)
        entries = self.load_all()
        changed = False
        for e in entries:
            if e.get("id") in id_set:
                e["uses"] = int(e.get("uses", 0) or 0) + 1
                changed = True
        if changed:
            self.save(entries)

    def delete_by_id(self, memory_id: str) -> bool:
        """Remove a single entry by id. Returns True if removed."""
        entries = self.load_all()
        remaining = [e for e in entries if e.get("id") != memory_id]
        if len(remaining) == len(entries):
            return False
        self.save(remaining)
        return True

    # ------------------------------------------------------------------
    # Dedup & relevance
    # ------------------------------------------------------------------

    def find_duplicates(self, text: str, entries: List[Dict] | None = None) -> List[Dict]:
        """Exact-text-match dedup."""
        if entries is None:
            entries = self.load_all()
        text_lower = text.strip().lower()
        return [e for e in entries if e.get("text", "").lower() == text_lower]

    def get_relevant_memories(
        self,
        query: str,
        memories: List[Dict] | None = None,
        threshold: float = 0.05,
        max_items: int = 8,
    ) -> List[Dict]:
        """Keyword + semantic-category boosted relevance search.

        Falls back to Jaccard similarity when the vector store is unavailable.
        This is the same algorithm Odysseus uses in ``MemoryManager.get_relevant_memories``.
        """
        if not memories:
            memories = self.load_all()
        if not memories or not query.strip():
            return []

        query_lower = query.lower()
        query_tokens = set(tokenize(query_lower))

        # Category keyword hints (same categories Odysseus uses)
        _identity_words = {"name", "who", "i", "am", "called", "identity", "myself", "me", "my"}
        _contact_words = {"phone", "email", "address", "contact", "number", "where", "located", "reach"}
        _preference_words = {"like", "prefer", "favorite", "want", "love", "hate", "dislike", "enjoy", "interested"}
        _task_words = {"todo", "task", "remind", "meeting", "appointment", "schedule", "deadline"}

        # Determine query type
        qtype = None
        if _identity_words & query_tokens:
            qtype = "identity"
        elif _contact_words & query_tokens:
            qtype = "contact"
        elif _preference_words & query_tokens:
            qtype = "preference"
        elif _task_words & query_tokens:
            qtype = "task"
        else:
            qtype = "fact"

        # Separate identity entries from the rest
        identity_memories = []
        other_memories = []
        _name_pattern = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")
        _id_indicators = {"name is", "i'm", "i am", "called", "my name", "named", "call me"}

        for mem in memories:
            text_lower = (mem.get("text") or "").lower()
            is_id = bool(_name_pattern.search(mem.get("text", ""))) or any(
                w in text_lower for w in _id_indicators
            )
            if is_id:
                identity_memories.append(mem)
            else:
                other_memories.append(mem)

        relevant: List[Tuple[float, Dict]] = []

        # Identity query → all identity memories get a high baseline score
        if qtype == "identity" and identity_memories:
            for mem in identity_memories:
                relevant.append((0.9, mem))

        for mem in other_memories:
            mem_text = (mem.get("text") or "").lower()
            mem_tokens = set(tokenize(mem_text))
            if not query_tokens or not mem_tokens:
                continue

            base = _jaccard(query_tokens, mem_tokens)
            score = base

            # Category boosts
            if qtype == "contact" and any(
                w in mem_text for w in ("@gmail.com", "@", ".com", "phone", "number", "address", "http", "www", "tel:")
            ):
                score *= 1.4
            elif qtype == "preference" and any(
                w in mem_text for w in ("like", "love", "hate", "dislike", "prefer", "favorite", "enjoy", "interested")
            ):
                score *= 1.3
            elif qtype == "task" and any(
                w in mem_text for w in ("todo", "task", "remind", "meeting", "appointment", "schedule", "deadline", "need to")
            ):
                score *= 1.3

            if query.lower() in mem.get("text", "").lower():
                score = max(score, 0.8)

            if score >= threshold:
                relevant.append((score, mem))

        relevant.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in relevant[:max_items]]

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _validate_entries(self, entries: List[Dict]) -> List[Dict]:
        """Ensure every entry has the required fields."""
        validated = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry.setdefault("id", str(uuid.uuid4()))
            entry.setdefault("timestamp", int(time.time()))
            entry.setdefault("source", "unknown")
            entry.setdefault("category", "fact")
            entry.setdefault("uses", 0)
            validated.append(entry)
        return validated
