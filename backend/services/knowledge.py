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
        document = self._document(document_id)
        if document is None:
            raise RuntimeError('document was not saved')
        return document

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
