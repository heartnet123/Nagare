"""Memory service — high-level remember / recall / list / delete API.

Port of Odysseus' ``services/memory/service.py``.  Orchestrates the JSON-backed
``MemoryManager`` and the optional ChromaDB ``MemoryVectorStore`` behind a
simple async interface that both REST routes and agent tools can use.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .manager import MemoryManager
from .provider import MemoryProviderRegistry, NativeMemoryProvider
from .vector import MemoryVectorStore


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Memory:
    """A stored memory returned to callers."""

    id: str
    text: str
    timestamp: int
    category: str = "fact"
    source: str = "user"
    owner: Optional[str] = None
    session_id: Optional[str] = None
    pinned: bool = False
    uses: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySearchResult:
    """Result of memory search."""

    memories: List[Memory]
    query: str
    total: int


# ---------------------------------------------------------------------------
# MemoryService
# ---------------------------------------------------------------------------


class MemoryService:
    """Unified memory storage and retrieval service.

    Usage::

        svc = MemoryService(data_dir)
        await svc.remember("User prefers dark mode")
        results = await svc.recall("preferences")
        all_memories = svc.get_all()
    """

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.manager = MemoryManager(self.data_dir / "agent_memory.json")

        vectors_dir = self.data_dir / "memory_vectors"
        self.vector_store = (
            MemoryVectorStore(self.data_dir) if vectors_dir.exists() else None
        )

        self.provider = NativeMemoryProvider(self.manager, self.vector_store)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    async def remember(
        self,
        text: str,
        *,
        owner: Optional[str] = None,
        session_id: Optional[str] = None,
        category: str = "fact",
        source: str = "user",
    ) -> Memory:
        """Store a new memory."""
        self._sync_provider()
        record = await self.provider.remember(
            text,
            owner=owner,
            session_id=session_id,
            category=category,
            source=source,
        )
        return self._record_to_memory(record)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def recall(self, query: str, top_k: int = 5) -> MemorySearchResult:
        """Search memories semantically (with keyword fallback)."""
        self._sync_provider()
        results = await self.provider.recall(query, top_k=top_k)
        memories = [
            self._record_to_memory(
                hit.memory,
                metadata={"score": hit.score} if hit.score is not None else None,
            )
            for hit in results
        ]
        return MemorySearchResult(memories=memories, query=query, total=len(memories))

    def get_all(self, limit: int = 100) -> List[Memory]:
        """Return all stored memories."""
        records = self.manager.load_all()[:limit]
        return [self._entry_to_memory(m) for m in records]

    def get_for_owner(self, owner: str, limit: int = 100) -> List[Memory]:
        """Return memories scoped to an owner."""
        return [
            self._entry_to_memory(m) for m in self.manager.load(owner=owner)[:limit]
        ]

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        removed = self.manager.delete_by_id(memory_id)
        if removed and self.vector_store and self.vector_store.healthy:
            self.vector_store.remove(memory_id)
        return removed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sync_provider(self) -> None:
        self.provider.memory_vector = self.vector_store

    @staticmethod
    def _entry_to_memory(entry: Dict[str, Any]) -> Memory:
        return Memory(
            id=entry.get("id", ""),
            text=entry.get("text", ""),
            timestamp=entry.get("timestamp", 0),
            category=entry.get("category", "fact"),
            source=entry.get("source", "user"),
            owner=entry.get("owner"),
            session_id=entry.get("session_id"),
            pinned=bool(entry.get("pinned", False)),
            uses=int(entry.get("uses", 0)),
        )

    @staticmethod
    def _record_to_memory(record, metadata: Optional[Dict] = None) -> Memory:
        merged = dict(record.metadata)
        if metadata:
            merged.update(metadata)
        return Memory(
            id=record.id,
            text=record.text,
            timestamp=record.timestamp,
            category=record.category,
            source=record.source,
            owner=record.owner,
            session_id=record.session_id,
            metadata=merged,
        )
