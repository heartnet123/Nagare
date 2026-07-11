from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from middleware.auth import get_current_user_from_cookie, validate_csrf_token
from models.knowledge import (
    KnowledgeChunkResponse,
    KnowledgeChunkPageResponse,
    KnowledgeDeleteResponse,
    KnowledgeDocumentResponse,
)
from services.knowledge import KnowledgeStore

MAX_UPLOAD_BYTES = 50 * 1024 * 1024

router = APIRouter(
    prefix="/api/knowledge",
    tags=["knowledge"],
    dependencies=[Depends(get_current_user_from_cookie)],
)


@router.post(
    "/upload",
    response_model=KnowledgeDocumentResponse,
    dependencies=[Depends(validate_csrf_token)],
)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document and index its contents in ChromaDB."""
    try:
        filename = Path(file.filename or "").name
        if not filename:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "File name is required")
        content = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File exceeds 50 MiB limit")
        if not content:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "File is empty")
        store = KnowledgeStore()
        doc = store.ingest_bytes(filename, content, file.content_type or "application/octet-stream")
        return doc
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    finally:
        await file.close()


@router.get("/documents", response_model=list[KnowledgeDocumentResponse])
async def list_documents():
    """List all indexed documents."""
    return KnowledgeStore().list_documents()


@router.get("/document/{doc_id}/chunks", response_model=KnowledgeChunkPageResponse)
async def list_document_chunks(
    doc_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    page = KnowledgeStore().list_chunks(doc_id, offset, limit)
    if page is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Document '{doc_id}' not found")
    return KnowledgeChunkPageResponse(
        items=[KnowledgeChunkResponse.model_validate(item) for item in page.items],
        total=page.total,
        offset=offset,
        limit=limit,
    )


@router.delete(
    "/document/{doc_id}",
    response_model=KnowledgeDeleteResponse,
    dependencies=[Depends(validate_csrf_token)],
)
async def delete_document(doc_id: str):
    """Delete a document by ID from DB and vector index."""
    deleted = KnowledgeStore().delete_document(doc_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Document '{doc_id}' not found")
    return {"status": "success", "message": f"Document '{doc_id}' deleted"}


@router.get("/search")
async def search_knowledge(q: str = Query(..., min_length=1), limit: int = Query(5, ge=1, le=20)):
    """Query the knowledge base vector database directly."""
    return KnowledgeStore().search(q, limit)
