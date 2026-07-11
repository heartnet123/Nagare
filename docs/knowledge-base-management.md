# Knowledge Base Management Architecture

## Scope

Knowledge management is a shared authenticated workspace over the existing SQLite metadata store and Chroma collection. Users can list indexed documents, inspect source chunks, upload supported files, search vectors, and delete a document with all associated chunks.

## Storage

No migration is required. Existing tables remain source of truth:

- `knowledge_documents`: document identity, source metadata, byte size, chunk count, creation time, file type.
- `knowledge_chunks`: ordered text chunks, source page, creation time, foreign key to document with `ON DELETE CASCADE`.
- Chroma collection `knowledge_fastembed`: embeddings keyed by chunk ID, with document ID and source metadata.

Document IDs remain deterministic SHA-256 values over filename plus bytes. Uploading the same filename and bytes refreshes the same document; renaming identical bytes creates a distinct document.

## Backend Flow

1. FastAPI authenticates every `/api/knowledge/**` request.
2. Upload and delete also validate the cookie CSRF header.
3. Upload reads at most 50 MiB plus one byte, parses supported formats, writes metadata/chunks to SQLite, then upserts vector records.
4. Chunk preview reads SQLite directly with deterministic `chunk_index, id` ordering and bounded pagination.
5. Delete removes vector IDs, then deletes the SQLite parent row; foreign-key cascade removes chunk rows.

## API Routes

| Method | Route | Response |
| --- | --- | --- |
| `GET` | `/api/knowledge/documents` | `KnowledgeDocument[]` |
| `GET` | `/api/knowledge/document/{id}/chunks?offset=0&limit=100` | `{ items, total, offset, limit }` |
| `POST` | `/api/knowledge/upload` | Uploaded `KnowledgeDocument` |
| `DELETE` | `/api/knowledge/document/{id}` | Status and message |
| `GET` | `/api/knowledge/search?q=...&limit=5` | Ranked chunk results |

## Frontend

`knowledge.vue` owns orchestration only. Focused components own upload, inventory, chunk preview, and semantic-search surfaces. `useApiKnowledge()` is typed and supplies cookie credentials plus CSRF headers on mutations.

## Operational Limits

- Supported: PDF, DOCX, TXT, Markdown, CSV, JSON, JSONL.
- Maximum upload: 50 MiB.
- Chunk pages: 1 to 500 records, 25 per page in UI.
- Current authorization scope: all authenticated users share one knowledge base. Per-user isolation requires adding `user_id` ownership to both document access and vector metadata.
