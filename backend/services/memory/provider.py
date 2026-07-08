"""Memory provider interfaces — provider pattern for native + external backends.

Port of Odysseus' ``src/memory_provider.py``.  The ``NativeMemoryProvider``
wraps the JSON-backed ``MemoryManager`` and optional ``MemoryVectorStore``
into a single async ``remember`` / ``recall`` contract.  Additional providers
(e.g.  external RAG services) can be plugged in via ``MemoryProviderRegistry``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class MemoryRecord:
    """Provider-neutral memory entry."""

    id: str
    text: str
    timestamp: int = 0
    category: str = "fact"
    source: str = "unknown"
    owner: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemorySearchHit:
    """A memory returned by provider recall."""

    memory: MemoryRecord
    provider_id: str
    score: Optional[float] = None


# ---------------------------------------------------------------------------
# Abstract provider
# ---------------------------------------------------------------------------


class MemoryProvider(ABC):
    """Base contract for memory providers.

    The native provider is always available; external providers can add
    recall/write behaviour without replacing the built-in baseline.
    """

    provider_id: str = "unknown"
    display_name: str = "Unknown"
    enabled: bool = True

    async def initialize(self) -> None:
        """Prepare provider resources before use."""

    async def shutdown(self) -> None:
        """Release provider resources."""

    @abstractmethod
    async def remember(
        self,
        text: str,
        *,
        owner: Optional[str] = None,
        session_id: Optional[str] = None,
        category: str = "fact",
        source: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        """Store a memory and return the stored record."""

    @abstractmethod
    async def recall(
        self,
        query: str,
        *,
        owner: Optional[str] = None,
        top_k: int = 5,
    ) -> List[MemorySearchHit]:
        """Return provider memories relevant to the query."""

    @abstractmethod
    async def list_memories(
        self,
        *,
        owner: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        """List memories visible to the owner."""

    @abstractmethod
    async def delete(self, memory_id: str, *, owner: Optional[str] = None) -> bool:
        """Delete a memory by ID when allowed by the provider."""

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return provider-defined tool schemas when this provider is enabled."""
        return []

    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Handle a provider-defined tool call."""
        raise KeyError(f"Provider {self.provider_id} does not expose tool {name}")


# ---------------------------------------------------------------------------
# Native provider
# ---------------------------------------------------------------------------


class NativeMemoryProvider(MemoryProvider):
    """Wraps the built-in MemoryManager + optional MemoryVectorStore."""

    provider_id = "native"
    display_name = "Nagare native memory"

    _CORE_FIELDS = {
        "id", "text", "timestamp", "source", "category",
        "uses", "owner", "session_id", "metadata",
    }

    def __init__(self, memory_manager, memory_vector=None):
        self.memory_manager = memory_manager
        self.memory_vector = memory_vector

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------

    def _to_record(self, entry: Dict[str, Any]) -> MemoryRecord:
        metadata = {
            key: value
            for key, value in entry.items()
            if key not in self._CORE_FIELDS
        }
        stored = entry.get("metadata")
        if isinstance(stored, dict):
            metadata.update(stored)
        return MemoryRecord(
            id=entry.get("id", ""),
            text=entry.get("text", ""),
            timestamp=entry.get("timestamp", 0),
            category=entry.get("category", "fact"),
            source=entry.get("source", "unknown"),
            owner=entry.get("owner"),
            session_id=entry.get("session_id"),
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Provider API
    # ------------------------------------------------------------------

    async def remember(
        self,
        text: str,
        *,
        owner: Optional[str] = None,
        session_id: Optional[str] = None,
        category: str = "fact",
        source: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryRecord:
        entry = self.memory_manager.add_entry(
            text,
            source=source,
            category=category,
            owner=owner,
        )
        if session_id:
            entry["session_id"] = session_id
        if metadata:
            entry["metadata"] = dict(metadata)

        memories = self.memory_manager.load_all()
        memories.append(entry)
        self.memory_manager.save(memories)

        if self._vector_available():
            self.memory_vector.add(entry["id"], entry["text"])

        return self._to_record(entry)

    async def recall(
        self,
        query: str,
        *,
        owner: Optional[str] = None,
        top_k: int = 5,
    ) -> List[MemorySearchHit]:
        memories = self.memory_manager.load(owner=owner)
        by_id = {m.get("id"): m for m in memories}

        # Try vector search first
        if self._vector_available():
            hits: List[MemorySearchHit] = []
            for result in self.memory_vector.search(query, k=top_k):
                if not isinstance(result, dict):
                    continue
                memory_id = result.get("memory_id")
                entry = by_id.get(memory_id) if memory_id else result
                if not entry:
                    continue
                if owner is not None and entry.get("owner") != owner:
                    continue
                hits.append(
                    MemorySearchHit(
                        memory=self._to_record(entry),
                        provider_id=self.provider_id,
                        score=result.get("score"),
                    )
                )
            if hits:
                return hits

        # Fallback to keyword / Jaccard
        fallback = self.memory_manager.get_relevant_memories(
            query, memories, max_items=top_k
        )
        return [
            MemorySearchHit(
                memory=self._to_record(entry),
                provider_id=self.provider_id,
                score=None,
            )
            for entry in fallback
        ]

    async def list_memories(
        self,
        *,
        owner: Optional[str] = None,
        limit: int = 100,
    ) -> List[MemoryRecord]:
        return [
            self._to_record(entry)
            for entry in self.memory_manager.load(owner=owner)[:limit]
        ]

    async def delete(self, memory_id: str, *, owner: Optional[str] = None) -> bool:
        memories = self.memory_manager.load_all()
        remaining = []
        deleted_id = None

        for entry in memories:
            if entry.get("id") != memory_id:
                remaining.append(entry)
                continue
            if owner is not None and entry.get("owner") != owner:
                remaining.append(entry)
                continue
            deleted_id = entry.get("id")

        if deleted_id is None:
            return False

        self.memory_manager.save(remaining)
        if self._vector_available():
            self.memory_vector.remove(deleted_id)
        return True

    def _vector_available(self) -> bool:
        return bool(self.memory_vector and getattr(self.memory_vector, "healthy", False))


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class MemoryProviderRegistry:
    """Container for native and optional external memory providers."""

    def __init__(self, providers: Optional[Iterable[MemoryProvider]] = None):
        self._providers: Dict[str, MemoryProvider] = {}
        for provider in providers or []:
            self.register(provider)

    def register(self, provider: MemoryProvider) -> None:
        if provider.provider_id in self._providers:
            raise ValueError(
                f"Memory provider already registered: {provider.provider_id}"
            )
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> MemoryProvider:
        return self._providers[provider_id]

    def all(self) -> List[MemoryProvider]:
        return list(self._providers.values())

    def active(self) -> List[MemoryProvider]:
        return [p for p in self._providers.values() if p.enabled]
