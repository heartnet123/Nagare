from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocumentResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    title: str
    source_name: str
    content_type: str
    size_bytes: int = Field(ge=0)
    chunk_count: int = Field(ge=0)
    created_at: str
    file_type: str | None = None


class KnowledgeChunkResponse(BaseModel):
    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: str
    document_id: str
    chunk_index: int = Field(ge=0)
    text: str
    created_at: str
    page_number: int | None = Field(default=None, ge=1)


class KnowledgeChunkPageResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    items: list[KnowledgeChunkResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1)


class KnowledgeDeleteResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: str
    message: str
