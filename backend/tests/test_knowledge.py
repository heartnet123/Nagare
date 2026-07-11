from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.testclient import TestClient
from middleware.auth import get_current_user_from_cookie, validate_csrf_token
from routers import knowledge
from services.knowledge import KnowledgeStore


@dataclass
class FakeCollection:
    records: dict[str, str] = field(default_factory=dict)
    deleted_ids: list[str] = field(default_factory=list)

    def upsert(
        self,
        *,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, str | int]],
    ) -> None:
        del metadatas
        self.records.update(zip(ids, documents, strict=True))

    def delete(self, *, ids: list[str]) -> None:
        self.deleted_ids.extend(ids)
        for chunk_id in ids:
            del self.records[chunk_id]


def test_document_chunks_are_paginated_and_deleted_with_document(tmp_path, monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(KnowledgeStore, '_collection', lambda _: collection)
    store = KnowledgeStore(tmp_path)
    text = ('retrieval context ' * 100).encode()

    document = store.ingest_bytes('handbook.txt', text)

    first_page = store.list_chunks(document['id'], offset=0, limit=1)
    assert first_page is not None
    assert first_page.total == document['chunk_count']
    assert len(first_page.items) == 1
    assert first_page.items[0].chunk_index == 0

    assert store.delete_document(document['id'])
    assert store.list_chunks(document['id'], offset=0, limit=1) is None
    assert not collection.records
    assert len(collection.deleted_ids) == document['chunk_count']


def test_knowledge_routes_manage_authenticated_documents(tmp_path, monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(KnowledgeStore, '_collection', lambda _: collection)
    monkeypatch.setattr(knowledge, 'KnowledgeStore', lambda: KnowledgeStore(tmp_path))

    app = FastAPI()
    app.include_router(knowledge.router)
    app.dependency_overrides[get_current_user_from_cookie] = lambda: {'id': 'operator'}
    app.dependency_overrides[validate_csrf_token] = lambda: None

    with TestClient(app) as client:
        uploaded = client.post(
            '/api/knowledge/upload',
            files={'file': ('guide.txt', b'retrieval context ' * 100, 'text/plain')},
        )
        assert uploaded.status_code == 200
        document = uploaded.json()

        listed = client.get('/api/knowledge/documents')
        assert listed.status_code == 200
        assert [item['id'] for item in listed.json()] == [document['id']]

        chunks = client.get(f"/api/knowledge/document/{document['id']}/chunks?limit=1")
        assert chunks.status_code == 200
        assert chunks.json()['total'] == document['chunk_count']
        assert len(chunks.json()['items']) == 1

        deleted = client.delete(f"/api/knowledge/document/{document['id']}")
        assert deleted.status_code == 200
        assert deleted.json()['status'] == 'success'

        missing = client.get(f"/api/knowledge/document/{document['id']}/chunks")
        assert missing.status_code == 404


def test_upload_rejects_files_larger_than_limit(tmp_path, monkeypatch):
    collection = FakeCollection()
    monkeypatch.setattr(KnowledgeStore, '_collection', lambda _: collection)
    monkeypatch.setattr(knowledge, 'KnowledgeStore', lambda: KnowledgeStore(tmp_path))
    monkeypatch.setattr(knowledge, 'MAX_UPLOAD_BYTES', 4)

    app = FastAPI()
    app.include_router(knowledge.router)
    app.dependency_overrides[get_current_user_from_cookie] = lambda: {'id': 'operator'}
    app.dependency_overrides[validate_csrf_token] = lambda: None

    with TestClient(app) as client:
        response = client.post(
            '/api/knowledge/upload',
            files={'file': ('large.txt', b'12345', 'text/plain')},
        )

    assert response.status_code == 413
