"""Session management API routes — list, create, rename, delete, archive sessions.

Port from Odysseus routes/session_routes.py, adapted to Nagare's
simplified patterns (no auth, no owner scoping, no endpoint model resolution).
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from models.session import (
    SessionCreateRequest,
    SessionListResponse,
    SessionResponse,
    SessionUpdateRequest,
)
from services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["sessions"])

_manager: SessionManager | None = None


def _register(sm: SessionManager):
    global _manager
    _manager = sm


async def _get_manager() -> SessionManager:
    if _manager is None:
        raise HTTPException(503, "Session manager not initialized")
    return _manager


def _session_to_response(s: dict) -> SessionResponse:
    """Convert internal session dict to response model."""
    return SessionResponse(
        id=s["id"],
        name=s["name"],
        model=s.get("model", ""),
        endpoint_url=s.get("endpoint_url", ""),
        rag=s.get("rag", False),
        archived=s.get("archived", False),
        is_important=s.get("is_important", False),
        folder=s.get("folder"),
        message_count=s.get("message_count", 0),
        total_input_tokens=s.get("total_input_tokens", 0),
        total_output_tokens=s.get("total_output_tokens", 0),
        created_at=s.get("created_at"),
        updated_at=s.get("updated_at"),
        last_accessed=s.get("last_accessed"),
        last_message_at=s.get("last_message_at"),
        has_documents=s.get("has_documents", False),
        has_images=s.get("has_images", False),
        mode=s.get("mode"),
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    search: str = Query("", description="Filter by name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List all active (non-archived) sessions."""
    mgr = await _get_manager()
    sessions_list, total = mgr.list_sessions(
        archived=False,
        limit=limit,
        offset=offset,
        search=search or None,
    )
    return SessionListResponse(
        sessions=[_session_to_response(s) for s in sessions_list],
        total=total,
    )


@router.get("/sessions/archived", response_model=SessionListResponse)
async def list_archived_sessions(
    search: str = Query("", description="Filter by name"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List archived sessions."""
    mgr = await _get_manager()
    sessions_list, total = mgr.list_sessions(
        archived=True,
        limit=limit,
        offset=offset,
        search=search or None,
    )
    return SessionListResponse(
        sessions=[_session_to_response(s) for s in sessions_list],
        total=total,
    )


@router.post("/session", response_model=SessionResponse, status_code=201)
async def create_session(body: SessionCreateRequest):
    """Create a new chat session."""
    mgr = await _get_manager()
    sid = str(uuid.uuid4())
    session = mgr.create_session(
        session_id=sid,
        name=body.name or "New Chat",
        model=body.model or "",
        endpoint_url=body.endpoint_url or "",
        mode=body.mode or "chat",
    )
    return _session_to_response(session)


@router.get("/session/{sid}", response_model=SessionResponse)
async def get_session(sid: str):
    """Get a single session by ID."""
    mgr = await _get_manager()
    try:
        session = mgr.get_session(sid)
    except KeyError:
        raise HTTPException(404, f"Session '{sid}' not found")
    return _session_to_response(session)


@router.patch("/session/{sid}", response_model=SessionResponse)
async def update_session(sid: str, body: SessionUpdateRequest):
    """Update session fields (name, folder, model)."""
    mgr = await _get_manager()
    try:
        # Verify session exists
        mgr.get_session(sid)
    except KeyError:
        raise HTTPException(404, f"Session '{sid}' not found")

    updated = mgr.update_session(
        session_id=sid,
        name=body.name,
        folder=body.folder,
        model=body.model,
    )
    if updated is None:
        raise HTTPException(404, f"Session '{sid}' not found")
    return _session_to_response(updated)


@router.delete("/session/{sid}")
async def delete_session(sid: str):
    """Permanently delete a session and all its messages."""
    mgr = await _get_manager()
    # Check exists first
    try:
        mgr.get_session(sid)
    except KeyError:
        raise HTTPException(404, f"Session '{sid}' not found")

    if mgr.delete_session(sid):
        return {"status": "deleted", "id": sid}
    raise HTTPException(500, "Failed to delete session")


@router.post("/session/{sid}/archive")
async def archive_session(sid: str):
    """Archive a session (hide from active list, keep data)."""
    mgr = await _get_manager()
    try:
        mgr.get_session(sid)
    except KeyError:
        raise HTTPException(404, f"Session '{sid}' not found")
    mgr.archive_session(sid, archived=True)
    return {"status": "archived", "id": sid}


@router.post("/session/{sid}/unarchive")
async def unarchive_session(sid: str):
    """Restore an archived session to the active list."""
    mgr = await _get_manager()
    try:
        mgr.get_session(sid)
    except KeyError:
        raise HTTPException(404, f"Session '{sid}' not found")
    mgr.archive_session(sid, archived=False)
    return {"status": "unarchived", "id": sid}


@router.post("/session/{sid}/important")
async def mark_important(sid: str, important: bool = True):
    """Mark a session as important (protected from auto-cleanup)."""
    mgr = await _get_manager()
    try:
        mgr.get_session(sid)
    except KeyError:
        raise HTTPException(404, f"Session '{sid}' not found")
    mgr.mark_important(sid, important=important)
    return {"status": "success", "is_important": important, "id": sid}
