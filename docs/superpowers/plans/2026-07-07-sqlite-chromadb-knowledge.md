# SQLite ChromaDB Knowledge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Knowledge data layer backed by SQLite metadata, ChromaDB vectors, and FastEmbed embeddings.

**Architecture:** Use stdlib `sqlite3` for canonical document/chunk records and a Chroma persistent collection for semantic chunk search. Keep backend logic in one focused service, expose it through a new FastAPI router, then connect chat tools and the Knowledge page to the same service.

**Tech Stack:** FastAPI, Pydantic v2, stdlib `sqlite3`, ChromaDB, FastEmbed, Nuxt/Vue, Tailwind utilities.

## Global Constraints

- Store SQLite at `backend/data/app.db` by default.
- Store Chroma data at `backend/data/chroma` by default.
- Add `chromadb`, `fastembed`, and `python-multipart` only.
- No ORM, Alembic, auth, workspaces, background jobs, PDF/DOCX parsing, or mock API rewrite outside Knowledge.
- Do not commit, push, publish, or deploy.
- Preserve existing untracked user files and unrelated changes.

---

## File Structure

- Create `backend/services/data.py`: data directory and SQLite schema setup.
- Create `backend/services/knowledge.py`: ingestion, chunking, Chroma upsert/query/delete, metadata operations.
- Create `backend/models/knowledge.py`: API schemas.
- Create `backend/routers/knowledge.py`: Knowledge endpoints.
- Modify `backend/main.py`: include Knowledge router.
- Modify `backend/services/agent/tools.py`: add `search_knowledge` handler.
- Modify `backend/services/agent/loop.py`: document `search_knowledge` in tool prompt.
- Modify `backend/requirements.txt`: add dependencies.
- Modify `backend/tests/test_agent_core.py`: add one focused service/tool test.
- Modify `frontend/app/composables/useApi.ts`: add knowledge client methods.
- Replace `frontend/app/pages/knowledge.vue`: upload/list/delete/search UI.

---

### Task 1: Backend Knowledge Store

**Files:**
- Create: `backend/services/data.py`
- Create: `backend/services/knowledge.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_agent_core.py`

**Interfaces:**
- Produces: `default_data_dir() -> Path`, `connect_db(data_dir: Path | None = None) -> sqlite3.Connection`, `init_db(conn: sqlite3.Connection) -> None`
- Produces: `KnowledgeStore(data_dir: Path | None = None)`
- Produces: `KnowledgeStore.ingest_bytes(filename: str, content: bytes, content_type: str = 'text/plain') -> dict`
- Produces: `KnowledgeStore.list_documents() -> list[dict]`
- Produces: `KnowledgeStore.search(query: str, limit: int = 5) -> list[dict]`
- Produces: `KnowledgeStore.delete_document(document_id: str) -> bool`

- [ ] **Step 1: Add dependency lines**

Add to `backend/requirements.txt`:

```text
chromadb==0.5.23
fastembed==0.4.2
python-multipart==0.0.12
```

- [ ] **Step 2: Write failing test**

Append to `backend/tests/test_agent_core.py`:

```python

def test_knowledge_store_ingests_and_searches_text():
    from services.knowledge import KnowledgeStore

    with tempfile.TemporaryDirectory() as tmp:
        store = KnowledgeStore(Path(tmp))
        document = store.ingest_bytes(
            'rag-notes.md',
            b'NAGARE uses semantic retrieval for knowledge base answers.',
            'text/markdown'
        )

        results = store.search('semantic retrieval answers', limit=3)

        assert document['source_name'] == 'rag-notes.md'
        assert document['chunk_count'] == 1
        assert results
        assert results[0]['document_id'] == document['id']
        assert 'semantic retrieval' in results[0]['text'].lower()
```

- [ ] **Step 3: Run test to verify fail before implementation**

Run:

```bash
cd backend && pytest tests/test_agent_core.py::test_knowledge_store_ingests_and_searches_text -v
```

Expected: fail with `ModuleNotFoundError: No module named 'services.knowledge'`.

- [ ] **Step 4: Create `backend/services/data.py`**

```python
from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = '''
create table if not exists knowledge_documents (
    id text primary key,
    title text not null,
    source_name text not null,
    content_type text not null,
    size_bytes integer not null,
    chunk_count integer not null,
    created_at text not null
);

create table if not exists knowledge_chunks (
    id text primary key,
    document_id text not null,
    chunk_index integer not null,
    text text not null,
    created_at text not null,
    foreign key (document_id) references knowledge_documents(id) on delete cascade
);

create index if not exists idx_knowledge_chunks_document_id
on knowledge_chunks(document_id);
'''


def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[1] / 'data'


def connect_db(data_dir: Path | None = None) -> sqlite3.Connection:
    root = data_dir or default_data_dir()
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(root / 'app.db')
    conn.row_factory = sqlite3.Row
    conn.execute('pragma foreign_keys = on')
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()
```

- [ ] **Step 5: Create `backend/services/knowledge.py`**

```python
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from .data import connect_db, default_data_dir


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 160
TEXT_EXTENSIONS = {'.txt', '.md', '.json', '.jsonl', '.csv'}


class KnowledgeStore:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or default_data_dir()
        self.conn = connect_db(self.data_dir)

    def ingest_bytes(self, filename: str, content: bytes, content_type: str = 'text/plain') -> dict:
        text = self._decode_text(filename, content)
        if not text.strip():
            raise ValueError('file is empty')

        document_id = hashlib.sha256(filename.encode('utf-8') + b'\0' + content).hexdigest()
        chunks = self._chunk_text(text)
        now = datetime.now(timezone.utc).isoformat()
        title = Path(filename).stem or filename

        with self.conn:
            self.conn.execute('delete from knowledge_chunks where document_id = ?', (document_id,))
            self.conn.execute('delete from knowledge_documents where id = ?', (document_id,))
            self.conn.execute(
                '''
                insert into knowledge_documents
                (id, title, source_name, content_type, size_bytes, chunk_count, created_at)
                values (?, ?, ?, ?, ?, ?, ?)
                ''',
                (document_id, title, filename, content_type, len(content), len(chunks), now)
            )
            rows = []
            for index, chunk in enumerate(chunks):
                chunk_id = self._chunk_id(document_id, index, chunk)
                rows.append((chunk_id, document_id, index, chunk, now))
            self.conn.executemany(
                '''
                insert into knowledge_chunks (id, document_id, chunk_index, text, created_at)
                values (?, ?, ?, ?, ?)
                ''',
                rows
            )

        self._collection().upsert(
            ids=[row[0] for row in rows],
            documents=[row[3] for row in rows],
            metadatas=[{
                'document_id': document_id,
                'chunk_index': row[2],
                'source': filename,
                'title': title
            } for row in rows]
        )
        return self._document(document_id)

    def list_documents(self) -> list[dict]:
        rows = self.conn.execute(
            'select * from knowledge_documents order by created_at desc'
        ).fetchall()
        return [dict(row) for row in rows]

    def search(self, query: str, limit: int = 5) -> list[dict]:
        query = query.strip()
        if not query:
            raise ValueError('query required')
        result = self._collection().query(query_texts=[query], n_results=max(1, min(limit, 20)))
        ids = result.get('ids', [[]])[0]
        documents = result.get('documents', [[]])[0]
        metadatas = result.get('metadatas', [[]])[0]
        distances = result.get('distances', [[]])[0]
        items = []
        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] or {}
            items.append({
                'id': chunk_id,
                'document_id': metadata.get('document_id', ''),
                'chunk_index': metadata.get('chunk_index', 0),
                'source': metadata.get('source', ''),
                'title': metadata.get('title', ''),
                'text': documents[index],
                'distance': distances[index] if index < len(distances) else None
            })
        return items

    def delete_document(self, document_id: str) -> bool:
        document = self._document(document_id)
        if document is None:
            return False
        chunk_rows = self.conn.execute(
            'select id from knowledge_chunks where document_id = ?',
            (document_id,)
        ).fetchall()
        chunk_ids = [row['id'] for row in chunk_rows]
        if chunk_ids:
            self._collection().delete(ids=chunk_ids)
        with self.conn:
            self.conn.execute('delete from knowledge_documents where id = ?', (document_id,))
        return True

    def _document(self, document_id: str) -> dict | None:
        row = self.conn.execute(
            'select * from knowledge_documents where id = ?',
            (document_id,)
        ).fetchone()
        return dict(row) if row else None

    def _collection(self):
        import chromadb
        from chromadb.utils.embedding_functions.fastembed_embedding_function import FastEmbedEmbeddingFunction

        client = chromadb.PersistentClient(path=str(self.data_dir / 'chroma'))
        embedding = FastEmbedEmbeddingFunction()
        return client.get_or_create_collection(
            name='knowledge_fastembed',
            embedding_function=embedding
        )

    def _decode_text(self, filename: str, content: bytes) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix and suffix not in TEXT_EXTENSIONS:
            raise ValueError('only UTF-8 text files are supported')
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError as exc:
            raise ValueError('only UTF-8 text files are supported') from exc

    def _chunk_text(self, text: str) -> list[str]:
        normalized = re.sub(r'\s+', ' ', text).strip()
        if len(normalized) <= CHUNK_SIZE:
            return [normalized]
        chunks = []
        start = 0
        while start < len(normalized):
            end = min(start + CHUNK_SIZE, len(normalized))
            chunks.append(normalized[start:end].strip())
            if end == len(normalized):
                break
            start = max(0, end - CHUNK_OVERLAP)
        return chunks

    def _chunk_id(self, document_id: str, index: int, text: str) -> str:
        raw = f'{document_id}:{index}:{text}'.encode('utf-8')
        return hashlib.sha256(raw).hexdigest()
```

- [ ] **Step 6: Run backend test**

Run:

```bash
cd backend && pytest tests/test_agent_core.py::test_knowledge_store_ingests_and_searches_text -v
```

Expected: pass, or fail only because dependencies are not installed / FastEmbed model download is unavailable.

---

### Task 2: Knowledge API

**Files:**
- Create: `backend/models/knowledge.py`
- Create: `backend/routers/knowledge.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_agent_core.py`

**Interfaces:**
- Consumes: `KnowledgeStore.ingest_bytes`, `list_documents`, `search`, `delete_document`
- Produces API response fields matching frontend: `id`, `title`, `source_name`, `content_type`, `size_bytes`, `chunk_count`, `created_at`, search result fields.

- [ ] **Step 1: Create models**

Create `backend/models/knowledge.py`:

```python
from pydantic import BaseModel


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    source_name: str
    content_type: str
    size_bytes: int
    chunk_count: int
    created_at: str


class KnowledgeSearchResult(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    source: str
    title: str
    text: str
    distance: float | None = None
```

- [ ] **Step 2: Create router**

Create `backend/routers/knowledge.py`:

```python
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from models.knowledge import KnowledgeDocument, KnowledgeSearchResult
from services.knowledge import KnowledgeStore


router = APIRouter(prefix='/api/knowledge', tags=['knowledge'])


def store() -> KnowledgeStore:
    return KnowledgeStore()


@router.get('/documents', response_model=list[KnowledgeDocument])
async def list_documents():
    return store().list_documents()


@router.post('/documents', response_model=KnowledgeDocument, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    try:
        return store().ingest_bytes(file.filename or 'upload.txt', content, file.content_type or 'text/plain')
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete('/documents/{document_id}', status_code=204)
async def delete_document(document_id: str):
    if not store().delete_document(document_id):
        raise HTTPException(status_code=404, detail='Document not found')


@router.get('/search', response_model=list[KnowledgeSearchResult])
async def search_knowledge(q: str = Query(min_length=1), limit: int = Query(default=5, ge=1, le=20)):
    try:
        return store().search(q, limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
```

- [ ] **Step 3: Mount router**

Modify `backend/main.py` imports and router list:

```python
from routers import evaluations, agents, datasets, monitoring, logs, chat, knowledge
```

```python
app.include_router(chat.router)
app.include_router(knowledge.router)
```

- [ ] **Step 4: Add API smoke test**

Append to `backend/tests/test_agent_core.py`:

```python

def test_knowledge_router_lists_documents_empty():
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    response = client.get('/api/knowledge/documents')

    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 5: Run API smoke test**

Run:

```bash
cd backend && pytest tests/test_agent_core.py::test_knowledge_router_lists_documents_empty -v
```

Expected: pass.

---

### Task 3: Agent Knowledge Tool

**Files:**
- Modify: `backend/services/agent/tools.py`
- Modify: `backend/services/agent/loop.py`
- Test: `backend/tests/test_agent_core.py`

**Interfaces:**
- Consumes: `KnowledgeStore.search(query: str, limit: int = 5) -> list[dict]`
- Produces tool: `search_knowledge` with args `{"query":"...","limit":5}` and JSON list output.

- [ ] **Step 1: Add tool test**

Append to `backend/tests/test_agent_core.py`:

```python

def test_knowledge_tool_requires_query():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / 'workspace'
        data_dir = Path(tmp) / 'data'
        workspace.mkdir()
        data_dir.mkdir()
        executor = ToolExecutor(workspace=workspace, data_dir=data_dir)

        result = executor.execute(ToolCall(name='search_knowledge', arguments={}))

        assert result.ok is False
        assert 'query required' in result.output
```

- [ ] **Step 2: Implement handler**

Modify `backend/services/agent/tools.py`:

```python
from .knowledge import KnowledgeStore
```

Add to `handlers`:

```python
            'search_knowledge': self._search_knowledge,
```

Add method before `_mcp_client`:

```python
    def _search_knowledge(self, args: dict) -> ToolResult:
        query = str(args.get('query', '')).strip()
        limit = int(args.get('limit', 5))
        if not query:
            return ToolResult(False, 'query required')
        results = KnowledgeStore(self.data_dir).search(query, limit)
        return ToolResult(True, json.dumps(results, indent=2))
```

- [ ] **Step 3: Update system prompt docs**

Modify `backend/services/agent/loop.py` `TOOL_DOCS` block by adding:

```text
search_knowledge: {"query":"semantic search terms","limit":5}
```

- [ ] **Step 4: Run tool test**

Run:

```bash
cd backend && pytest tests/test_agent_core.py::test_knowledge_tool_requires_query -v
```

Expected: pass.

---

### Task 4: Frontend Knowledge Page

**Files:**
- Modify: `frontend/app/composables/useApi.ts`
- Modify: `frontend/app/pages/knowledge.vue`

**Interfaces:**
- Consumes: `GET /api/knowledge/documents`
- Consumes: `POST /api/knowledge/documents` with `FormData` field `file`
- Consumes: `DELETE /api/knowledge/documents/{id}`
- Consumes: `GET /api/knowledge/search?q=...&limit=5`

- [ ] **Step 1: Add API methods**

Modify `frontend/app/composables/useApi.ts` return object before `monitoring`:

```ts
    knowledge: {
      list: () => $fetch('/api/knowledge/documents', { baseURL }),
      upload: (file: File) => {
        const body = new FormData()
        body.append('file', file)
        return $fetch('/api/knowledge/documents', {
          method: 'POST',
          body,
          baseURL
        })
      },
      remove: (id: string) => $fetch(`/api/knowledge/documents/${id}`, {
        method: 'DELETE',
        baseURL
      }),
      search: (q: string, limit = 5) => $fetch('/api/knowledge/search', {
        query: { q, limit },
        baseURL
      })
    },
```

- [ ] **Step 2: Replace Knowledge page**

Replace `frontend/app/pages/knowledge.vue` with a page containing:

```vue
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { BookOpen, FileText, Search, Trash2, Upload } from '@lucide/vue'

definePageMeta({
  layout: 'default'
})

interface KnowledgeDocument {
  id: string
  title: string
  source_name: string
  content_type: string
  size_bytes: number
  chunk_count: number
  created_at: string
}

interface SearchResult {
  id: string
  document_id: string
  source: string
  title: string
  text: string
  distance: number | null
}

const api = useApi()
const documents = ref<KnowledgeDocument[]>([])
const results = ref<SearchResult[]>([])
const query = ref('')
const busy = ref(false)
const searching = ref(false)
const errorText = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const totalChunks = computed(() => documents.value.reduce((sum, doc) => sum + doc.chunk_count, 0))
const totalSize = computed(() => documents.value.reduce((sum, doc) => sum + doc.size_bytes, 0))

const formatBytes = (value: number) => {
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

const loadDocuments = async () => {
  documents.value = await api.knowledge.list() as KnowledgeDocument[]
}

const uploadFile = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  busy.value = true
  errorText.value = ''
  try {
    await api.knowledge.upload(file)
    await loadDocuments()
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : 'Upload failed'
  } finally {
    busy.value = false
    input.value = ''
  }
}

const removeDocument = async (id: string) => {
  busy.value = true
  errorText.value = ''
  try {
    await api.knowledge.remove(id)
    documents.value = documents.value.filter((doc) => doc.id !== id)
    results.value = results.value.filter((result) => result.document_id !== id)
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : 'Delete failed'
  } finally {
    busy.value = false
  }
}

const search = async () => {
  const text = query.value.trim()
  if (!text) return
  searching.value = true
  errorText.value = ''
  try {
    results.value = await api.knowledge.search(text, 5) as SearchResult[]
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : 'Search failed'
  } finally {
    searching.value = false
  }
}

onMounted(loadDocuments)
</script>

<template>
  <DashboardPageScroll>
    <DashboardPageHeader
      title="Knowledge"
      description="Upload text sources, index them locally, and preview semantic retrieval results."
    >
      <template #action>
        <input
          ref="fileInput"
          type="file"
          class="hidden"
          accept=".txt,.md,.json,.jsonl,.csv,text/*"
          @change="uploadFile"
        >
        <button
          class="flex items-center gap-2 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white text-sm font-medium shadow-sm transition-colors"
          :disabled="busy"
          @click="fileInput?.click()"
        >
          <Upload :size="16" :stroke-width="2" />
          Upload
        </button>
      </template>
    </DashboardPageHeader>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
      <DashboardStatCard :icon="BookOpen" label="Documents" :value="String(documents.length)" trend="local" />
      <DashboardStatCard :icon="FileText" label="Chunks" :value="String(totalChunks)" trend="indexed" />
      <DashboardStatCard :icon="Upload" label="Storage" :value="formatBytes(totalSize)" trend="SQLite + Chroma" />
    </div>

    <div v-if="errorText" class="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      {{ errorText }}
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_420px] gap-6">
      <section class="rounded-2xl bg-white border border-stone-200 shadow-sm overflow-hidden">
        <div class="px-5 py-4 border-b border-stone-100 flex items-center justify-between">
          <h2 class="text-sm font-semibold text-stone-900">Indexed documents</h2>
          <span class="text-xs text-stone-400">{{ documents.length }} total</span>
        </div>
        <div v-if="documents.length" class="divide-y divide-stone-100">
          <div v-for="doc in documents" :key="doc.id" class="p-5 flex items-start gap-4">
            <div class="p-2.5 rounded-xl bg-stone-50 text-stone-600">
              <FileText :size="20" :stroke-width="1.5" />
            </div>
            <div class="min-w-0 flex-1">
              <div class="text-sm font-semibold text-stone-900 truncate">{{ doc.title }}</div>
              <div class="text-xs text-stone-500 mt-1 truncate">{{ doc.source_name }}</div>
              <div class="flex flex-wrap gap-2 mt-3 text-[11px] text-stone-500">
                <span class="rounded-full bg-stone-100 px-2 py-1">{{ doc.chunk_count }} chunks</span>
                <span class="rounded-full bg-stone-100 px-2 py-1">{{ formatBytes(doc.size_bytes) }}</span>
              </div>
            </div>
            <button
              class="p-2 text-stone-300 hover:text-red-600 transition-colors"
              aria-label="Delete document"
              :disabled="busy"
              @click="removeDocument(doc.id)"
            >
              <Trash2 :size="16" />
            </button>
          </div>
        </div>
        <div v-else class="p-10 text-center text-sm text-stone-500">
          No documents indexed.
        </div>
      </section>

      <section class="rounded-2xl bg-white border border-stone-200 shadow-sm overflow-hidden">
        <div class="px-5 py-4 border-b border-stone-100">
          <h2 class="text-sm font-semibold text-stone-900">Search preview</h2>
        </div>
        <div class="p-5">
          <form class="flex gap-2 mb-4" @submit.prevent="search">
            <input
              v-model="query"
              class="min-w-0 flex-1 rounded-xl border border-stone-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
              placeholder="Search knowledge"
            >
            <button
              class="shrink-0 rounded-xl bg-stone-900 px-3 py-2 text-white disabled:opacity-60"
              :disabled="searching || !query.trim()"
              aria-label="Search"
            >
              <Search :size="16" />
            </button>
          </form>

          <div v-if="results.length" class="space-y-3">
            <article v-for="result in results" :key="result.id" class="rounded-xl border border-stone-200 p-3">
              <div class="text-xs font-semibold text-stone-900 mb-1">{{ result.title || result.source }}</div>
              <p class="text-xs leading-relaxed text-stone-600 line-clamp-5">{{ result.text }}</p>
            </article>
          </div>
          <div v-else class="text-sm text-stone-500 py-8 text-center">
            Search indexed text sources.
          </div>
        </div>
      </section>
    </div>
  </DashboardPageScroll>
</template>
```

- [ ] **Step 3: Run frontend type/lint check if available**

Run:

```bash
cd frontend && pnpm lint
```

Expected: pass. If script missing, report skipped.

---

### Task 5: Verification

**Files:**
- Review changed files from Tasks 1-4.

**Interfaces:**
- Confirms all earlier produced interfaces are wired.

- [ ] **Step 1: Run targeted backend tests**

Run:

```bash
cd backend && pytest tests/test_agent_core.py -v
```

Expected: pass, or dependency/model-download failure reported exactly.

- [ ] **Step 2: Run import smoke check**

Run:

```bash
cd backend && python - <<'PY'
from main import app
print([route.path for route in app.routes if 'knowledge' in route.path])
PY
```

Expected output includes:

```text
/api/knowledge/documents
/api/knowledge/search
```

- [ ] **Step 3: Inspect diff**

Run:

```bash
git diff -- backend frontend/app/pages/knowledge.vue frontend/app/composables/useApi.ts docs/superpowers/specs/2026-07-07-sqlite-chromadb-knowledge-design.md docs/superpowers/plans/2026-07-07-sqlite-chromadb-knowledge.md
```

Expected: only planned files changed.

- [ ] **Step 4: Final report**

Report:

- Files changed.
- Tests/checks run and exact pass/fail state.
- Any skipped checks and why.
- Remaining risk: first FastEmbed model download may be slow.

---

## Self-Review

- Spec coverage: SQLite metadata, Chroma vectors, FastEmbed, API, frontend page, agent tool, dependencies, focused test all covered.
- Placeholder scan: no TBD/TODO/implement-later wording remains.
- Type consistency: `KnowledgeStore` methods and API response fields are consistent across backend, tools, and frontend.
- Scope check: mock APIs outside Knowledge stay untouched.
