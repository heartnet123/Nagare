"""Pydantic models for the memory API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    """Request body for adding a memory."""

    text: str = Field(..., min_length=1, description="Memory content")
    category: str = Field("fact", description="identity | preference | fact | contact | project | goal")
    source: str = Field("user", description="user | auto | learned")
    session_id: Optional[str] = None


class MemoryResponse(BaseModel):
    """A stored memory."""

    id: str
    text: str
    timestamp: int
    category: str = "fact"
    source: str = "user"
    owner: Optional[str] = None
    session_id: Optional[str] = None
    pinned: bool = False
    uses: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MemorySearchRequest(BaseModel):
    """Request body for memory search."""

    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=50)


class MemorySearchResponse(BaseModel):
    """Search results."""

    memories: List[MemoryResponse]
    query: str
    total: int


class MemoryListResponse(BaseModel):
    """List of all memories."""

    memories: List[MemoryResponse]
    total: int


class MemoryDeleteResponse(BaseModel):
    """Result of delete operation."""

    ok: bool
    memory_id: str


class MemoryExtractRequest(BaseModel):
    """Request body for extraction."""

    messages: List[Dict[str, Any]] = Field(..., description="Chat messages to analyze")
    session_id: Optional[str] = None


class MemoryExtractResponse(BaseModel):
    """Result of memory extraction."""

    added: int = 0


class MemoryAuditResponse(BaseModel):
    """Result of memory audit."""

    before: int
    after: int
    error: Optional[str] = None
