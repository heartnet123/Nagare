import pytest
import sqlite3
import tempfile
from pathlib import Path
from services.data import connect_db, init_db
from services.session_manager import SessionManager
from models.session import SessionCreateRequest, SessionResponse
from services.agent.llm import AgentSettings
from services.agent.loop import build_system_prompt

def test_db_migration_adds_mode_column():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / 'app.db'
        # Create an old schema without the mode column
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('''
            create table sessions (
                id text primary key,
                name text not null,
                model text not null default '',
                endpoint_url text not null default '',
                rag integer not null default 0,
                archived integer not null default 0,
                is_important integer not null default 0,
                folder text,
                message_count integer not null default 0,
                total_input_tokens integer not null default 0,
                total_output_tokens integer not null default 0,
                created_at text not null,
                updated_at text not null,
                last_accessed text,
                last_message_at text
            );
        ''')
        conn.commit()
        
        # Verify mode is NOT in columns
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row["name"] for row in cursor.fetchall()]
        assert "mode" not in columns
        
        # Run init_db which performs migration
        init_db(conn)
        
        # Verify mode IS in columns now
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row["name"] for row in cursor.fetchall()]
        assert "mode" in columns
        conn.close()

def test_session_manager_stores_and_loads_mode(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        # Mock connect_db to use our temporary db
        def mock_connect_db():
            conn = sqlite3.connect(data_dir / 'app.db')
            conn.row_factory = sqlite3.Row
            conn.execute('pragma foreign_keys = on')
            init_db(conn)
            return conn
            
        monkeypatch.setattr("services.session_manager.connect_db", mock_connect_db)
        
        mgr = SessionManager()
        # Create session with default mode (chat)
        session1 = mgr.create_session("s1", "Session 1")
        assert session1["mode"] == "chat"
        
        # Create session with agent mode
        session2 = mgr.create_session("s2", "Session 2", mode="agent")
        assert session2["mode"] == "agent"
        
        # Retrieve from cache
        cached1 = mgr.get_session("s1")
        assert cached1["mode"] == "chat"
        
        # Force retrieve from DB
        mgr.sessions.clear()
        db_session1 = mgr.get_session("s1")
        assert db_session1["mode"] == "chat"
        
        db_session2 = mgr.get_session("s2")
        assert db_session2["mode"] == "agent"

def test_build_system_prompt_excludes_tools():
    # If tools is False, the prompt should not mention tool definitions or TOOL_DOCS
    prompt_with_tools = build_system_prompt(memories=[], skills=[], tools=True)
    prompt_without_tools = build_system_prompt(memories=[], skills=[], tools=False)
    
    assert '<tool name="read_file">' in prompt_with_tools
    assert '<tool name="read_file">' not in prompt_without_tools
    assert 'Available tools:' not in prompt_without_tools
