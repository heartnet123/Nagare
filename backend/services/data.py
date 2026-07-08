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
