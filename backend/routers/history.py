"""Chat history API routes — get messages for a session.

Port from Odysseus routes/session_routes.py get_history endpoint.
"""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException, Query

from models.session import ChatMessageResponse
from services.session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/history", tags=["history"])

_manager: SessionManager | None = None


def _register(sm: SessionManager):
    global _manager
    _manager = sm


async def _get_manager() -> SessionManager:
    if _manager is None:
        raise HTTPException(503, "Session manager not initialized")
    return _manager


@router.get("/{sid}", response_model=List[ChatMessageResponse])
async def get_history(sid: str):
    """Get full message history for a session."""
    mgr = await _get_manager()
    try:
        messages = mgr.get_messages(sid)
    except KeyError:
        raise HTTPException(404, f"Session '{sid}' not found")

    return [
        ChatMessageResponse(
            id=m["id"],
            role=m["role"],
            content=m["content"],
            metadata=m.get("metadata"),
            timestamp=m.get("timestamp", ""),
        )
        for m in messages
    ]
