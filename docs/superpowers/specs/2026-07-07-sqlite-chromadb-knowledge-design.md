# SQLite + ChromaDB Knowledge Design

## Goal

Add a local knowledge-base data layer for NAGARE using SQLite for document metadata, ChromaDB for semantic retrieval, and FastEmbed for local embeddings. This replaces the Knowledge placeholder with a usable ingest/search flow and gives the chat agent a `search_knowledge` tool.

## Success Criteria

- Backend persists uploaded knowledge documents under `backend/data/app.db` and vectors under `backend/data/chroma`.
- Knowledge API supports document list, upload, delete, and semantic search.
- Frontend Knowledge page can upload a text-like file, show indexed documents, delete documents, and preview search results.
- Chat agent can retrieve knowledge chunks through a tool call.
- One focused backend test proves ingest and search work with a temporary data directory.

## Current Context

- Backend is FastAPI with mock domain routers and a streaming local agent.
- Agent memory currently uses a JSON file in `backend/services/agent/memory.py`.
- Knowledge page is a placeholder at `frontend/app/pages/knowledge.vue`.
- `backend/requirements.txt` only has FastAPI, Uvicorn, Pydantic, and dotenv.
- Odysseus uses SQLite plus ChromaDB, stable SHA-256 document IDs, persistent vector storage, and FastEmbed as local embedding fallback.

## Scope

In scope:

- Add SQLite helper and schema initialization for knowledge documents and chunks.
- Add Chroma persistent client with FastEmbed embeddings.
- Add text ingestion, chunking, semantic search, and delete-by-document.
- Add Knowledge API and minimal Knowledge UI.
- Add `search_knowledge` agent tool.

Out of scope:

- Auth, workspaces, multi-tenant owners.
- PDF/DOCX parsing.
- Background indexing jobs.
- Multiple embedding lanes or model registry integration.
- Replacing existing agents/datasets/evaluations/logs mock APIs.
- PostgreSQL/Alembic from the old roadmap.

## Architecture

Use the smallest local stack:

- `backend/services/data.py`: stdlib `sqlite3` connection, `data_dir()` helper, schema init.
- `backend/services/knowledge.py`: ingest, chunk, vector upsert/query/delete, SQLite metadata.
- `backend/models/knowledge.py`: Pydantic request/response models.
- `backend/routers/knowledge.py`: API endpoints mounted from `backend/main.py`.
- `frontend/app/pages/knowledge.vue`: real page replacing placeholder.
- `frontend/app/composables/useApi.ts`: knowledge API methods.

SQLite stores canonical document/chunk metadata. Chroma stores chunk embeddings and searchable text. Chroma metadata includes `document_id`, `chunk_index`, `source`, and `title` so search results can link back to documents.

## Data Model

SQLite tables:

- `knowledge_documents(id text primary key, title text, source_name text, content_type text, size_bytes integer, chunk_count integer, created_at text)`
- `knowledge_chunks(id text primary key, document_id text, chunk_index integer, text text, created_at text)`

IDs:

- Document ID: SHA-256 of source name plus content bytes.
- Chunk ID: SHA-256 of document ID plus chunk index plus chunk text.

This mirrors Odysseus stable hash behavior without owner-scoping because NAGARE has no auth/workspace boundary yet.

## API

- `GET /api/knowledge/documents`: list documents newest first.
- `POST /api/knowledge/documents`: multipart upload, text-like files only.
- `DELETE /api/knowledge/documents/{document_id}`: remove SQLite rows and matching Chroma vectors.
- `GET /api/knowledge/search?q=...&limit=5`: return semantic matches.

Upload accepts `.txt`, `.md`, `.json`, `.jsonl`, `.csv`, and other UTF-8 text. Non-UTF-8 input returns a 400.

## Agent Flow

Add tool docs and executor handler:

- `search_knowledge`: `{"query":"question","limit":5}`

Handler calls the same knowledge service and returns compact source snippets. Existing chat streaming behavior stays unchanged.

## Error Handling

- Missing query returns 400 or tool failure.
- Empty upload returns 400.
- Chroma/FastEmbed import or runtime failure surfaces as a clear API/tool error.
- Delete is idempotent only for existing document IDs; missing documents return 404.

## Dependencies

Add to `backend/requirements.txt`:

- `chromadb`
- `fastembed`
- `python-multipart`

No ORM. No migration package. No new frontend dependencies.

## Testing

Add one backend test around `KnowledgeStore` using a temp data directory:

- ingest a short text document.
- search for a semantic phrase contained in the text.
- assert returned result includes the document title/source and chunk text.

If FastEmbed model download is unavailable in the environment, report that test as blocked by dependency/model fetch rather than claiming pass.

## Risks

- First FastEmbed run may download a model and be slow.
- Chroma package install may be heavier than current backend deps.
- Semantic ranking quality depends on default FastEmbed model.

## Approval Gates

- Do not commit.
- Do not delete user-created files.
- Do not replace mock APIs outside Knowledge.
- Do not start a long-running server unless needed for verification.

## Completion Criteria

- Code diff matches this scope.
- Targeted backend test run attempted and result reported.
- Knowledge page points at real API methods.
- Agent tool documentation includes `search_knowledge`.

## Self-Review

- No placeholders remain.
- PostgreSQL roadmap conflict resolved by explicitly choosing SQLite per current request.
- Scope limited to Knowledge plus agent search tool.
- Multi-user owner-scoping deferred until auth/workspaces exist.
