"""Memory vector store — ChromaDB-backed semantic search.

Port of Odysseus' ``src/memory_vector.py``, adapted to Nagare's existing
ChromaDB + FastEmbed pattern from ``services/knowledge.py``.

Provides semantic similarity search, near-duplicate detection, and full
index rebuild.  When ChromaDB is not installed, all operations degrade
gracefully (no-op) so the keyword fallback in ``MemoryManager`` is always
available.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb
    # Use ChromaDB's built-in default embedding (all-MiniLM-L6-v2) when
    # fastembed is not installed.  This avoids an extra dependency and
    # works with the base ``chromadb`` package.
    import chromadb.utils.embedding_functions as ef

    _FASTEMBED_AVAILABLE = True
    try:
        from chromadb.utils.embedding_functions.fastembed_embedding_function import (  # noqa: F401
            FastEmbedEmbeddingFunction,
        )
    except ImportError:
        _FASTEMBED_AVAILABLE = False

    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False
    logger.warning("chromadb not installed — vector memory will be unavailable")


# ---------------------------------------------------------------------------
# MemoryVectorStore
# ---------------------------------------------------------------------------


class MemoryVectorStore:
    """Vector index over memory entries.

    Wraps a single ChromaDB collection named ``{prefix}_memories``
    (default ``odysseus_memories``) with a FastEmbed embedding function.

    Usage::

        vs = MemoryVectorStore(str(data_dir))
        vs.add("mem-1", "User prefers dark mode")
        results = vs.search("dark mode", k=5)
        vs.remove("mem-1")
    """

    COLLECTION_PREFIX = "nagare"

    def __init__(self, data_dir: str):
        self._data_dir = data_dir
        self._collection = None
        self._healthy = False
        self._initialize()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _initialize(self) -> None:
        if not _CHROMA_AVAILABLE:
            self._healthy = False
            return
        try:
            client = chromadb.PersistentClient(path=str(self._data_dir / "chroma"))
            if _FASTEMBED_AVAILABLE:
                from chromadb.utils.embedding_functions.fastembed_embedding_function import (  # noqa: F811
                    FastEmbedEmbeddingFunction,
                )
                embedding = FastEmbedEmbeddingFunction()
            else:
                embedding = ef.DefaultEmbeddingFunction()
            self._collection = client.get_or_create_collection(
                name=f"{self.COLLECTION_PREFIX}_memories",
                embedding_function=embedding,
            )
            self._healthy = True
            logger.info(
                "MemoryVectorStore ready (collection=%s, count=%d, embedding=%s)",
                self._collection.name,
                self.count(),
                "fastembed" if _FASTEMBED_AVAILABLE else "default",
            )
        except Exception as exc:
            self._healthy = False
            logger.error("MemoryVectorStore init failed: %s", exc)

    @property
    def healthy(self) -> bool:
        return self._healthy

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def count(self) -> int:
        """Return number of stored vectors."""
        if not self._healthy or self._collection is None:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0

    def add(self, memory_id: str, text: str) -> None:
        """Add or update a single memory entry in the vector index."""
        if not self._healthy or self._collection is None:
            return
        try:
            self._collection.add(
                ids=[memory_id],
                documents=[text],
                metadatas=[{"source": "memory"}],
            )
        except Exception as exc:
            logger.warning("MemoryVectorStore.add(%s) failed: %s", memory_id, exc)

    def remove(self, memory_id: str) -> None:
        """Delete a single entry from the index (O(1))."""
        if not self._healthy or self._collection is None:
            return
        try:
            self._collection.delete(ids=[memory_id])
        except Exception as exc:
            logger.warning("MemoryVectorStore.remove(%s) failed: %s", memory_id, exc)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, k: int = 8) -> List[Dict[str, Any]]:
        """Semantic search.

        Returns::

            [{"memory_id": str, "score": float, "document": str}, ...]

        ``score`` is cosine similarity (1.0 = identical).
        Empty list on failure or when the index is empty.
        """
        if not self._healthy or self._collection is None or self.count() == 0:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(k, self.count()),
                include=["documents", "distances"],
            )
            out = []
            for idx, mid in enumerate(results["ids"][0]):
                distance = results["distances"][0][idx] if results.get("distances") else 0.0
                out.append({
                    "memory_id": mid,
                    "score": round(1.0 - distance, 4),
                    "document": results["documents"][0][idx] if results.get("documents") else "",
                })
            return out
        except Exception as exc:
            logger.warning("MemoryVectorStore.search failed: %s", exc)
            return []

    def find_similar(self, text: str, threshold: float = 0.92) -> Optional[str]:
        """Check if a near-duplicate exists.

        Returns the *memory_id* of the closest match if similarity ≥ *threshold*,
        otherwise ``None``.
        """
        if not self._healthy or self._collection is None or self.count() == 0:
            return None
        try:
            results = self._collection.query(
                query_texts=[text],
                n_results=1,
                include=["distances"],
            )
            if results["ids"][0]:
                distance = results["distances"][0][0]
                similarity = 1.0 - distance
                if similarity >= threshold:
                    return results["ids"][0][0]
        except Exception as exc:
            logger.warning("MemoryVectorStore.find_similar failed: %s", exc)
        return None

    # ------------------------------------------------------------------
    # Rebuild
    # ------------------------------------------------------------------

    def rebuild(self, memories: List[Dict]) -> None:
        """Delete and re-insert all entries.

        Each dict in *memories* must have ``id`` and ``text`` keys.
        Batches of 100 to avoid oversized requests.
        """
        if not self._healthy or self._collection is None:
            return

        # Collect valid entries
        texts: List[str] = []
        mids: List[str] = []
        for mem in memories:
            text = (mem.get("text") or "").strip()
            mid = mem.get("id", "")
            if text and mid:
                texts.append(text)
                mids.append(mid)

        # Delete & re-create collection
        try:
            name = self._collection.name
            client = chromadb.PersistentClient(path=str(self._data_dir / "chroma"))
            embedding = FastEmbedEmbeddingFunction()
            client.delete_collection(name)
            self._collection = client.get_or_create_collection(
                name=name,
                embedding_function=embedding,
            )
        except Exception as exc:
            logger.error("MemoryVectorStore rebuild (drop) failed: %s", exc)
            return

        if not texts:
            return

        try:
            for i in range(0, len(texts), 100):
                batch_texts = texts[i : i + 100]
                batch_ids = mids[i : i + 100]
                self._collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=[{"source": "memory"}] * len(batch_ids),
                )
            logger.info("MemoryVectorStore rebuilt with %d entries", len(mids))
        except Exception as exc:
            logger.error("MemoryVectorStore rebuild (insert) failed: %s", exc)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        return {
            "healthy": self.healthy,
            "count": self.count(),
        }
