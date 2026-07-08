from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re

from .data import connect_db, default_data_dir


CHUNK_SIZE = 1200
CHUNK_OVERLAP = 160
TEXT_EXTENSIONS = {'.txt', '.md', '.json', '.jsonl', '.csv', '.pdf', '.docx'}


class KnowledgeStore:
    def __init__(self, data_dir: Path | None = None):
        self.data_dir = data_dir or default_data_dir()
        self.conn = connect_db(self.data_dir)

    def _parse_and_chunk(self, filename: str, content: bytes) -> list[tuple[str, int]]:
        """Parses document bytes and chunks them, returning list of (chunk_text, page_number)."""
        suffix = Path(filename).suffix.lower()
        chunks: list[tuple[str, int]] = []

        if suffix == '.pdf':
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=content, filetype="pdf")
                for page_idx, page in enumerate(doc):
                    page_text = page.get_text()
                    if page_text.strip():
                        page_chunks = self._chunk_text(page_text)
                        for chunk in page_chunks:
                            chunks.append((chunk, page_idx + 1))
            except Exception as exc:
                raise ValueError(f"Failed to parse PDF file: {exc}")
        elif suffix == '.docx':
            try:
                import docx
                from io import BytesIO
                doc = docx.Document(BytesIO(content))
                current_text = []
                current_length = 0
                page_num = 1
                for p in doc.paragraphs:
                    if not p.text.strip():
                        continue
                    current_text.append(p.text)
                    current_length += len(p.text)
                    if current_length >= 1000:
                        combined = " ".join(current_text)
                        for chunk in self._chunk_text(combined):
                            chunks.append((chunk, page_num))
                        current_text = []
                        current_length = 0
                        page_num += 1
                if current_text:
                    combined = " ".join(current_text)
                    for chunk in self._chunk_text(combined):
                        chunks.append((chunk, page_num))
            except Exception as exc:
                raise ValueError(f"Failed to parse DOCX file: {exc}")
        else:
            # TXT, MD, CSV, JSON
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text = content.decode('latin-1')
                except Exception as exc:
                    raise ValueError(f"Failed to decode text file: {exc}")

            if not text.strip():
                raise ValueError('file is empty')
            
            raw_chunks = self._chunk_text(text)
            for chunk in raw_chunks:
                chunks.append((chunk, 1))

        return chunks

    def ingest_bytes(self, filename: str, content: bytes, content_type: str = 'text/plain') -> dict:
        suffix = Path(filename).suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            raise ValueError(f"File extension {suffix} is not supported. Supported: {', '.join(TEXT_EXTENSIONS)}")

        chunks = self._parse_and_chunk(filename, content)
        if not chunks:
            raise ValueError('Document contains no extractable text.')

        document_id = hashlib.sha256(filename.encode('utf-8') + b'\0' + content).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        title = Path(filename).stem or filename

        with self.conn:
            self.conn.execute('delete from knowledge_chunks where document_id = ?', (document_id,))
            self.conn.execute('delete from knowledge_documents where id = ?', (document_id,))
            self.conn.execute(
                '''
                insert into knowledge_documents
                (id, title, source_name, content_type, size_bytes, chunk_count, created_at, file_type)
                values (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (document_id, title, filename, content_type, len(content), len(chunks), now, suffix[1:])
            )
            rows = []
            for index, (chunk_text, page_num) in enumerate(chunks):
                chunk_id = self._chunk_id(document_id, index, chunk_text)
                rows.append((chunk_id, document_id, index, chunk_text, now, page_num))
            self.conn.executemany(
                '''
                insert into knowledge_chunks (id, document_id, chunk_index, text, created_at, page_number)
                values (?, ?, ?, ?, ?, ?)
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
                'title': title,
                'page_number': row[5],
                'file_type': suffix[1:]
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
            dist = distances[index] if index < len(distances) else None
            # Standard Cosine distance to confidence score conversion
            confidence = round(max(0.0, min(1.0, 1.0 - (dist if dist is not None else 0.5))), 2)
            items.append({
                'id': chunk_id,
                'document_id': metadata.get('document_id', ''),
                'chunk_index': metadata.get('chunk_index', 0),
                'source': metadata.get('source', ''),
                'title': metadata.get('title', ''),
                'page_number': metadata.get('page_number', 1),
                'file_type': metadata.get('file_type', 'txt'),
                'text': documents[index],
                'distance': dist,
                'confidence': confidence
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

