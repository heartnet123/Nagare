from __future__ import annotations

import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from services.knowledge import KnowledgeStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and index its contents in ChromaDB."""
    try:
        content = await file.read()
        if not content:
            raise HTTPException(400, "File is empty")
        
        store = KnowledgeStore()
        doc = store.ingest_bytes(file.filename, content, file.content_type)
        return doc
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    except Exception as exc:
        logger.error(f"Failed to upload document: {exc}", exc_info=True)
        raise HTTPException(500, f"Upload and indexing failed: {exc}")


@router.get("/documents")
async def list_documents():
    """List all indexed documents."""
    try:
        store = KnowledgeStore()
        return store.list_documents()
    except Exception as exc:
        logger.error(f"Failed to list documents: {exc}", exc_info=True)
        raise HTTPException(500, str(exc))


@router.delete("/document/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by ID from DB and vector index."""
    try:
        store = KnowledgeStore()
        deleted = store.delete_document(doc_id)
        if not deleted:
            raise HTTPException(404, f"Document '{doc_id}' not found")
        return {"status": "success", "message": f"Document '{doc_id}' deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Failed to delete document: {exc}", exc_info=True)
        raise HTTPException(500, str(exc))


@router.get("/search")
async def search_knowledge(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)):
    """Query the knowledge base vector database directly."""
    try:
        store = KnowledgeStore()
        results = store.search(q, limit)
        return results
    except Exception as exc:
        logger.error(f"Failed to search: {exc}", exc_info=True)
        raise HTTPException(500, str(exc))
