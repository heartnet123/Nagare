"""Pydantic models for chat sessions and messages."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessageResponse(BaseModel):
    """A single chat message in API responses."""

    id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str


class SessionResponse(BaseModel):
    """A chat session as returned by the API."""

    id: str
    name: str
    model: str = ""
    endpoint_url: str = ""
    rag: bool = False
    archived: bool = False
    is_important: bool = False
    folder: Optional[str] = None
    message_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_accessed: Optional[str] = None
    last_message_at: Optional[str] = None
    has_documents: bool = False
    has_images: bool = False
    mode: Optional[str] = None


class SessionCreateRequest(BaseModel):
    """Request body for creating a session."""

    name: str = "New Chat"
    model: str = ""
    endpoint_url: str = ""
    mode: Optional[str] = "chat"


class SessionUpdateRequest(BaseModel):
    """Request body for updating a session."""

    name: Optional[str] = None
    folder: Optional[str] = None
    model: Optional[str] = None


class SessionListResponse(BaseModel):
    """List of sessions."""

    sessions: List[SessionResponse]
    total: int
