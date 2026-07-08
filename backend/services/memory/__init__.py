"""Memory system — persistent storage, semantic retrieval, and LLM-driven extraction.

Port of the Odysseus memory system into Nagare. Provides:
- MemoryManager:  JSON-backed file store with keyword / fuzzy / Jaccard search
- MemoryVectorStore:  ChromaDB-backed vector store for semantic similarity
- MemoryService:  Unified remember / recall / list / delete API
- MemoryExtractor:  Background LLM extraction of durable facts from chat
- SkillsManager:  Disk-backed SKILL.md skill repository
"""

from __future__ import annotations

from .manager import MemoryManager, get_text_similarity, tokenize
from .service import MemoryService, Memory, MemorySearchResult
from .provider import NativeMemoryProvider, MemoryProviderRegistry

__all__ = [
    "MemoryManager",
    "MemoryService",
    "Memory",
    "MemorySearchResult",
    "NativeMemoryProvider",
    "MemoryProviderRegistry",
    "get_text_similarity",
    "tokenize",
]
