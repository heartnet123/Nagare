"""Memory API routes — CRUD, search, and extraction endpoints.

Port of Odysseus' ``routes/memory_routes.py`` adapted for Nagare.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from models.memory import (
    MemoryAuditResponse,
    MemoryCreate,
    MemoryDeleteResponse,
    MemoryExtractRequest,
    MemoryExtractResponse,
    MemoryListResponse,
    MemoryResponse,
    MemorySearchRequest,
    MemorySearchResponse,
)
from services.memory import MemoryService

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/memory", tags=["memory"])

# Lazy-init'd singleton (set on first use)
_service: Optional[MemoryService] = None


def _get_service() -> MemoryService:
    global _service
    if _service is None:
        from services.data import default_data_dir
        _service = MemoryService(default_data_dir())
    return _service


# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------


def _memory_to_response(memory) -> MemoryResponse:
    return MemoryResponse(
        id=memory.id,
        text=memory.text,
        timestamp=memory.timestamp,
        category=memory.category,
        source=memory.source,
        owner=memory.owner,
        session_id=memory.session_id,
        pinned=getattr(memory, "pinned", False),
        uses=getattr(memory, "uses", 0),
        metadata=getattr(memory, "metadata", {}),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=MemoryListResponse)
async def list_memories(limit: int = Query(100, ge=1, le=500)):
    """List all stored memories."""
    svc = _get_service()
    memories = svc.get_all(limit=limit)
    return MemoryListResponse(
        memories=[_memory_to_response(m) for m in memories],
        total=len(memories),
    )


@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(req: MemorySearchRequest):
    """Semantic search across memories."""
    svc = _get_service()
    result = await svc.recall(req.query, top_k=req.top_k)
    return MemorySearchResponse(
        memories=[_memory_to_response(m) for m in result.memories],
        query=result.query,
        total=result.total,
    )


@router.post("/add", response_model=MemoryResponse, status_code=201)
async def add_memory(req: MemoryCreate):
    """Add a new memory."""
    svc = _get_service()
    memory = await svc.remember(
        text=req.text,
        category=req.category,
        source=req.source,
        session_id=req.session_id,
    )
    return _memory_to_response(memory)


@router.delete("/{memory_id}", response_model=MemoryDeleteResponse)
async def delete_memory(memory_id: str):
    """Delete a memory by ID."""
    svc = _get_service()
    ok = svc.delete(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryDeleteResponse(ok=True, memory_id=memory_id)


@router.post("/extract", response_model=MemoryExtractResponse)
async def extract_memories(req: MemoryExtractRequest):
    """Analyze chat messages and extract durable facts.

    Uses the LLM configured in the environment to extract facts from
    the provided message history.
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    from services.memory.extractor import extract_and_store

    svc = _get_service()
    llm_call = _build_llm_call()

    added = await extract_and_store(
        svc.manager,
        svc.vector_store,
        req.messages,
        llm_call,
        owner=None,
        session_id=req.session_id,
    )
    return MemoryExtractResponse(added=added)


@router.post("/audit", response_model=MemoryAuditResponse)
async def audit_memories():
    """Run memory audit: dedup, consolidate, remove junk."""
    from services.memory.extractor import audit_memories as run_audit

    svc = _get_service()
    llm_call = _build_llm_call()

    result = await run_audit(
        svc.manager,
        svc.vector_store,
        llm_call,
        owner=None,
    )
    return MemoryAuditResponse(
        before=result.get("before", 0),
        after=result.get("after", 0),
        error=result.get("error"),
    )


@router.post("/claim", response_model=dict)
async def claim_ownerless(owner: str = Query(..., min_length=1)):
    """Assign all ownerless memories to the given owner."""
    svc = _get_service()
    count = svc.manager.claim_ownerless(owner)
    return {"claimed": count}


# ---------------------------------------------------------------------------
# LLM call helper
# ---------------------------------------------------------------------------


def _build_llm_call():
    """Return an async callable that sends messages to the configured LLM.

    Reads ``LLM_BASE_URL``, ``LLM_API_KEY``, and ``LLM_MODEL`` from the
    environment (matching Nagare's existing ``AgentSettings.from_env()``
    pattern).  Falls back to a no-op that returns ``[]`` on any call so the
    extractor degrades gracefully.
    """
    import os

    base_url = os.getenv("LLM_BASE_URL", "").rstrip("/")
    api_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "")

    if not base_url or not model:
        logger = __import__("logging").getLogger(__name__)
        logger.warning("LLM not configured — memory extraction will use fallback patterns only")

        async def _noop(messages):
            return "[]"
        return _noop

    import httpx

    async def _call(messages: list) -> str:
        url = f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return "[]"

    return _call
