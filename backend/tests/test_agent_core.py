from pathlib import Path
import tempfile

from services.agent.memory import MemoryStore
from services.agent.tools import ToolCall, ToolExecutor, parse_tool_blocks


def test_parse_tool_blocks_strips_xml_and_returns_calls():
    visible, calls = parse_tool_blocks('hello <tool name="read_file">{"path":"ROADMAP.md"}</tool> done')

    assert visible == 'hello  done'
    assert len(calls) == 1
    assert calls[0].name == 'read_file'
    assert calls[0].arguments == {'path': 'ROADMAP.md'}


def test_file_tool_rejects_workspace_escape():
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / 'workspace'
        data_dir = Path(tmp) / 'data'
        workspace.mkdir()
        data_dir.mkdir()
        executor = ToolExecutor(workspace=workspace, data_dir=data_dir)

        result = executor.execute(ToolCall(name='read_file', arguments={'path': '../secret.txt'}))

        assert result.ok is False
        assert 'outside workspace' in result.output


def test_memory_add_and_recall():
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(Path(tmp) / 'memory.json')

        saved = store.add('NAGARE evaluates RAG and agent systems')
        results = store.search('rag agent')

        assert saved['text'] == 'NAGARE evaluates RAG and agent systems'
        assert results[0]['text'] == 'NAGARE evaluates RAG and agent systems'
