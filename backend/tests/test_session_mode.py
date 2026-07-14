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


class MockSessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, session_id, name, model="", endpoint_url="", mode="chat"):
        session = {
            "id": session_id,
            "name": name,
            "model": model,
            "endpoint_url": endpoint_url,
            "mode": mode,
            "messages": [],
            "message_count": 0,
        }
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id):
        if session_id not in self.sessions:
            raise KeyError(session_id)
        return self.sessions[session_id]

    def add_message(self, session_id, role, content, metadata=None):
        session = self.get_session(session_id)
        msg = {
            "id": f"msg-{len(session['messages'])}",
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }
        session["messages"].append(msg)
        session["message_count"] = len(session["messages"])
        return msg

    def get_messages(self, session_id):
        session = self.get_session(session_id)
        return session["messages"]

    def replace_messages(self, session_id, messages):
        session = self.get_session(session_id)
        session["messages"] = list(messages)
        session["message_count"] = len(messages)
        return True


@pytest.mark.anyio
async def test_chat_stream_mode_chat_async(monkeypatch):
    import routers.chat
    from routers.chat import chat_stream, ChatStreamRequest, ChatMessage
    from services.agent.llm import OpenAICompatibleClient

    # Setup mock session manager
    mock_mgr = MockSessionManager()
    orig_mgr = routers.chat._session_manager
    routers.chat._register(mock_mgr)

    # Pre-create session with mode="chat"
    session_id = "test-chat-stream-session"
    mock_mgr.create_session(session_id=session_id, name="Test Chat", mode="chat")

    # Mock stream_chat
    async def mock_stream_chat(self, messages, model):
        yield "Hello! "
        yield '<tool name="read_file">{"path":"ROADMAP.md"}</tool>'
        yield " Done."

    monkeypatch.setattr(OpenAICompatibleClient, "stream_chat", mock_stream_chat)

    try:
        payload = ChatStreamRequest(
            session_id=session_id,
            messages=[ChatMessage(role="user", content="Hello, bot!")],
        )
        response = await chat_stream(payload)
        
        # Verify it is a StreamingResponse
        from fastapi.responses import StreamingResponse
        assert isinstance(response, StreamingResponse)

        # Parse SSE events from response.body_iterator
        events = []
        async for chunk in response.body_iterator:
            if chunk:
                events.append(chunk)

        # Check events returned
        has_tool_start = any("event: tool_start" in line for line in events)
        has_tool_result = any("event: tool_result" in line for line in events)
        assert not has_tool_start
        assert not has_tool_result

        # Verify that the session only has:
        # 1. User message (added at start or passed)
        # 2. Assistant message (added at end)
        # and no tool messages.
        msgs = mock_mgr.get_messages(session_id)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"
        # The assistant content should have the tool call stripped out
        assert msgs[1]["content"] == "Hello!  Done."

    finally:
        routers.chat._register(orig_mgr)


@pytest.mark.anyio
async def test_chat_regenerate(monkeypatch):
    import routers.chat
    from routers.chat import chat_regenerate, RegenerateRequest
    from services.agent.llm import OpenAICompatibleClient

    # Setup mock session manager
    mock_mgr = MockSessionManager()
    orig_mgr = routers.chat._session_manager
    routers.chat._register(mock_mgr)

    # Pre-create session with mode="chat"
    session_id = "test-regenerate-session"
    mock_mgr.create_session(session_id=session_id, name="Test Regenerate", mode="chat")

    # Add historical messages: user message, assistant message
    mock_mgr.add_message(session_id, "user", "Message 1", metadata={"source": "user"})
    mock_mgr.add_message(session_id, "assistant", "Response 1", metadata={"source": "assistant"})
    mock_mgr.add_message(session_id, "user", "Message 2", metadata={"source": "user"})
    mock_mgr.add_message(session_id, "assistant", "Response 2", metadata={"source": "assistant"})

    # Mock stream_chat to return a new response
    async def mock_stream_chat(self, messages, model):
        yield "Regenerated Response"

    monkeypatch.setattr(OpenAICompatibleClient, "stream_chat", mock_stream_chat)

    try:
        payload = RegenerateRequest(session_id=session_id)
        response = await chat_regenerate(payload)

        # Parse SSE events from response.body_iterator to consume the generator
        events = []
        async for chunk in response.body_iterator:
            if chunk:
                events.append(chunk)

        # Verify that the session messages were updated correctly.
        # "Response 2" should be deleted, and the history should now end with "Regenerated Response".
        # So we expect 4 messages:
        # 1. Message 1 (user)
        # 2. Response 1 (assistant)
        # 3. Message 2 (user)
        # 4. Regenerated Response (assistant)
        msgs = mock_mgr.get_messages(session_id)
        assert len(msgs) == 4
        assert msgs[0]["content"] == "Message 1"
        assert msgs[1]["content"] == "Response 1"
        assert msgs[2]["content"] == "Message 2"
        assert msgs[3]["content"] == "Regenerated Response"
        assert msgs[3]["role"] == "assistant"

    finally:
        routers.chat._register(orig_mgr)
