# Chat + Agents Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace mock chat with a working frontend + backend + AI streaming agent loop with files, shell, skills, memory, and basic MCP support.

**Architecture:** Add a small `backend/services/agent` package and a FastAPI SSE router. The Nuxt chat component streams from `/api/chat/stream`, renders assistant deltas, and shows tool events. State stays local and file-backed because NAGARE OS has no DB/auth foundation yet.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, stdlib HTTP/JSON/subprocess/pathlib, Nuxt 4, Vue 3, TypeScript.

## Global Constraints

- LLM backend: OpenAI-compatible chat completions.
- `AGENT_OPENAI_BASE_URL` default: `http://localhost:11434/v1`.
- `AGENT_OPENAI_API_KEY` default: `ollama`.
- `AGENT_MODEL` default: `llama3.1`.
- `AGENT_MAX_ROUNDS` default: `8`.
- `AGENT_WORKSPACE` default: repository root.
- Tool protocol: XML blocks like `<tool name="read_file">{"path":"README.md"}</tool>`.
- Memory store: `backend/data/agent_memory.json`.
- Skills store: `backend/data/skills/*.md`.
- MCP config: `backend/data/mcp_servers.json`.
- No DB, auth, native function-calling, remote MCP transports, vector memory, or file upload UI in this slice.
- Use stdlib first. Add no new dependency unless code cannot work without it.

---

## File Structure

- Create `backend/services/agent/__init__.py`: package marker and exported names.
- Create `backend/services/agent/memory.py`: JSON memory read/write/search.
- Create `backend/services/agent/skills.py`: Markdown skill listing/reading.
- Create `backend/services/agent/tools.py`: XML parser, workspace-safe file tools, shell tool, dispatch registry.
- Create `backend/services/agent/llm.py`: OpenAI-compatible streaming client.
- Create `backend/services/agent/mcp.py`: minimal stdio MCP JSON-RPC client.
- Create `backend/services/agent/loop.py`: prompt assembly, multi-round streaming loop, SSE event helpers.
- Create `backend/routers/chat.py`: request models and `StreamingResponse` endpoint.
- Modify `backend/main.py`: include chat router.
- Create `backend/data/skills/project.md`: seed skill.
- Create `backend/data/agent_memory.json`: empty JSON array.
- Create `backend/data/mcp_servers.json`: empty config.
- Create `backend/tests/test_agent_core.py`: assert-based backend checks.
- Modify `frontend/app/components/chat/ChatView.vue`: replace mock timer with SSE client and tool rendering.

---

### Task 1: Memory, Skills, Parser, and Local Tools

**Files:**
- Create: `backend/services/agent/__init__.py`
- Create: `backend/services/agent/memory.py`
- Create: `backend/services/agent/skills.py`
- Create: `backend/services/agent/tools.py`
- Create: `backend/data/skills/project.md`
- Create: `backend/data/agent_memory.json`
- Test: `backend/tests/test_agent_core.py`

**Interfaces:**
- Produces: `MemoryStore(path: Path)`, methods `add(text: str) -> dict`, `search(query: str, limit: int = 5) -> list[dict]`, `all() -> list[dict]`.
- Produces: `SkillsStore(root: Path)`, methods `list() -> list[dict]`, `read(name: str) -> str`.
- Produces: `parse_tool_blocks(text: str) -> tuple[str, list[ToolCall]]`.
- Produces: `ToolExecutor(workspace: Path, data_dir: Path, enable_shell: bool = True)`, method `execute(call: ToolCall) -> ToolResult`.

- [ ] **Step 1: Create failing backend checks**

Create `backend/tests/test_agent_core.py`:

```python
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
```

- [ ] **Step 2: Run checks to verify they fail**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: FAIL with import error for `services.agent.memory`.

- [ ] **Step 3: Create package marker**

Create `backend/services/agent/__init__.py`:

```python
"""Small local agent runtime for NAGARE chat."""
```

- [ ] **Step 4: Implement JSON memory store**

Create `backend/services/agent/memory.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4


class MemoryStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    def all(self) -> list[dict]:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            data = []
        return data if isinstance(data, list) else []

    def _write(self, items: list[dict]) -> None:
        self.path.write_text(json.dumps(items, indent=2), encoding='utf-8')

    def add(self, text: str) -> dict:
        item = {
            'id': str(uuid4()),
            'text': text.strip(),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        items = self.all()
        items.append(item)
        self._write(items)
        return item

    def search(self, query: str, limit: int = 5) -> list[dict]:
        terms = [part.lower() for part in query.split() if part.strip()]
        if not terms:
            return self.all()[-limit:]

        scored = []
        for item in self.all():
            text = str(item.get('text', '')).lower()
            score = sum(1 for term in terms if term in text)
            if score:
                scored.append((score, item))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]
```

- [ ] **Step 5: Implement Markdown skills store**

Create `backend/services/agent/skills.py`:

```python
from __future__ import annotations

from pathlib import Path


class SkillsStore:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def list(self) -> list[dict]:
        skills = []
        for path in sorted(self.root.glob('*.md')):
            content = path.read_text(encoding='utf-8')
            title = path.stem
            for line in content.splitlines():
                if line.startswith('#'):
                    title = line.lstrip('#').strip() or title
                    break
            skills.append({'name': path.stem, 'title': title})
        return skills

    def read(self, name: str) -> str:
        safe_name = Path(name).stem
        path = self.root / f'{safe_name}.md'
        if not path.exists():
            raise FileNotFoundError(f'skill not found: {safe_name}')
        return path.read_text(encoding='utf-8')
```

- [ ] **Step 6: Implement tool parser and executor**

Create `backend/services/agent/tools.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess

from .memory import MemoryStore
from .skills import SkillsStore


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    output: str


TOOL_RE = re.compile(r'<tool\s+name="([A-Za-z0-9_\-]+)">\s*(.*?)\s*</tool>', re.DOTALL)
DENIED_SHELL_PATTERNS = ('rm -rf', 'del /s', 'format ', 'shutdown', ':(){')


def parse_tool_blocks(text: str) -> tuple[str, list[ToolCall]]:
    calls: list[ToolCall] = []

    def collect(match: re.Match) -> str:
        name = match.group(1)
        raw = match.group(2).strip()
        try:
            args = json.loads(raw) if raw else {}
        except json.JSONDecodeError as exc:
            args = {'_parse_error': str(exc), '_raw': raw}
        calls.append(ToolCall(name=name, arguments=args if isinstance(args, dict) else {'value': args}))
        return ''

    visible = TOOL_RE.sub(collect, text)
    return visible, calls


class ToolExecutor:
    def __init__(self, workspace: Path, data_dir: Path, enable_shell: bool = True):
        self.workspace = workspace.resolve()
        self.data_dir = data_dir
        self.enable_shell = enable_shell
        self.memory = MemoryStore(data_dir / 'agent_memory.json')
        self.skills = SkillsStore(data_dir / 'skills')

    def execute(self, call: ToolCall) -> ToolResult:
        if '_parse_error' in call.arguments:
            return ToolResult(False, f'invalid tool JSON: {call.arguments["_parse_error"]}')

        handlers = {
            'list_files': self._list_files,
            'read_file': self._read_file,
            'write_file': self._write_file,
            'search_files': self._search_files,
            'run_shell': self._run_shell,
            'remember': self._remember,
            'recall': self._recall,
            'list_skills': self._list_skills,
            'use_skill': self._use_skill
        }
        handler = handlers.get(call.name)
        if handler is None:
            return ToolResult(False, f'unknown tool: {call.name}')
        try:
            return handler(call.arguments)
        except Exception as exc:
            return ToolResult(False, f'{call.name} failed: {exc}')

    def _safe_path(self, raw: str = '.') -> Path:
        candidate = (self.workspace / raw).resolve()
        if candidate != self.workspace and self.workspace not in candidate.parents:
            raise ValueError(f'path outside workspace: {raw}')
        return candidate

    def _list_files(self, args: dict) -> ToolResult:
        path = self._safe_path(str(args.get('path', '.')))
        depth = int(args.get('depth', 1))
        if not path.exists():
            return ToolResult(False, f'path not found: {path.relative_to(self.workspace)}')
        items = []
        for child in sorted(path.rglob('*') if depth > 1 else path.iterdir()):
            if '.git' in child.parts:
                continue
            rel = child.relative_to(self.workspace)
            items.append(f'{rel}/' if child.is_dir() else str(rel))
            if len(items) >= 200:
                break
        return ToolResult(True, '\n'.join(items))

    def _read_file(self, args: dict) -> ToolResult:
        path = self._safe_path(str(args.get('path', '')))
        if not path.is_file():
            return ToolResult(False, f'file not found: {path.relative_to(self.workspace)}')
        return ToolResult(True, path.read_text(encoding='utf-8'))

    def _write_file(self, args: dict) -> ToolResult:
        path = self._safe_path(str(args.get('path', '')))
        content = str(args.get('content', ''))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        return ToolResult(True, f'wrote {path.relative_to(self.workspace)}')

    def _search_files(self, args: dict) -> ToolResult:
        pattern = str(args.get('pattern', ''))
        root = self._safe_path(str(args.get('path', '.')))
        if not pattern:
            return ToolResult(False, 'pattern required')
        regex = re.compile(pattern, re.IGNORECASE)
        matches = []
        for path in root.rglob('*'):
            if '.git' in path.parts or not path.is_file():
                continue
            try:
                for number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                    if regex.search(line):
                        matches.append(f'{path.relative_to(self.workspace)}:{number}: {line[:200]}')
                        break
            except UnicodeDecodeError:
                continue
            if len(matches) >= 50:
                break
        return ToolResult(True, '\n'.join(matches) if matches else 'no matches')

    def _run_shell(self, args: dict) -> ToolResult:
        if not self.enable_shell:
            return ToolResult(False, 'shell disabled')
        command = str(args.get('command', '')).strip()
        timeout = min(int(args.get('timeout', 20)), 60)
        lowered = command.lower()
        if not command:
            return ToolResult(False, 'command required')
        if any(pattern in lowered for pattern in DENIED_SHELL_PATTERNS):
            return ToolResult(False, 'command denied by safety policy')
        completed = subprocess.run(
            command,
            cwd=self.workspace,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout
        )
        output = f'exit_code={completed.returncode}\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}'
        return ToolResult(completed.returncode == 0, output.strip())

    def _remember(self, args: dict) -> ToolResult:
        text = str(args.get('text', '')).strip()
        if not text:
            return ToolResult(False, 'text required')
        item = self.memory.add(text)
        return ToolResult(True, json.dumps(item))

    def _recall(self, args: dict) -> ToolResult:
        query = str(args.get('query', ''))
        return ToolResult(True, json.dumps(self.memory.search(query), indent=2))

    def _list_skills(self, args: dict) -> ToolResult:
        return ToolResult(True, json.dumps(self.skills.list(), indent=2))

    def _use_skill(self, args: dict) -> ToolResult:
        name = str(args.get('name', ''))
        if not name:
            return ToolResult(False, 'name required')
        return ToolResult(True, self.skills.read(name))
```

- [ ] **Step 7: Seed data files**

Create `backend/data/skills/project.md`:

```markdown
# NAGARE Project Context

NAGARE OS evaluates, monitors, and operates RAG and agent systems from one workspace.
Use short, grounded answers and cite tool output when available.
```

Create `backend/data/agent_memory.json`:

```json
[]
```

- [ ] **Step 8: Run backend checks**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: `3 passed`.

- [ ] **Step 9: Commit task**

```bash
git add backend/services/agent backend/data/skills/project.md backend/data/agent_memory.json backend/tests/test_agent_core.py
git commit -m "feat: add local agent tools and memory"
```

---

### Task 2: OpenAI-Compatible LLM Client and Agent Loop

**Files:**
- Create: `backend/services/agent/llm.py`
- Create: `backend/services/agent/loop.py`
- Modify: `backend/tests/test_agent_core.py`

**Interfaces:**
- Consumes: `parse_tool_blocks(text)`, `ToolExecutor.execute(call)` from Task 1.
- Produces: `AgentSettings.from_env() -> AgentSettings`.
- Produces: `OpenAICompatibleClient.stream_chat(messages: list[dict], model: str) -> async iterator[str]`.
- Produces: `stream_agent(messages: list[dict], settings: AgentSettings) -> async iterator[dict]` yielding event dictionaries `{event: str, data: dict}`.

- [ ] **Step 1: Extend checks for visible text filtering**

Append to `backend/tests/test_agent_core.py`:

```python
from services.agent.loop import build_system_prompt, sse_pack


def test_sse_pack_formats_event_and_json_data():
    packed = sse_pack('delta', {'content': 'hi'})

    assert packed.startswith('event: delta\n')
    assert 'data: {"content": "hi"}\n\n' in packed


def test_system_prompt_mentions_tool_protocol():
    prompt = build_system_prompt(memories=[], skills=[])

    assert '<tool name="read_file">' in prompt
    assert 'run_shell' in prompt
```

- [ ] **Step 2: Run checks to verify they fail**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: FAIL with import error for `services.agent.loop`.

- [ ] **Step 3: Implement OpenAI-compatible streaming client**

Create `backend/services/agent/llm.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from urllib import error, request


@dataclass(frozen=True)
class AgentSettings:
    base_url: str
    api_key: str
    model: str
    max_rounds: int

    @classmethod
    def from_env(cls) -> 'AgentSettings':
        return cls(
            base_url=os.getenv('AGENT_OPENAI_BASE_URL', 'http://localhost:11434/v1').rstrip('/'),
            api_key=os.getenv('AGENT_OPENAI_API_KEY', 'ollama'),
            model=os.getenv('AGENT_MODEL', 'llama3.1'),
            max_rounds=int(os.getenv('AGENT_MAX_ROUNDS', '8'))
        )


class OpenAICompatibleClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    async def stream_chat(self, messages: list[dict], model: str):
        payload = json.dumps({
            'model': model,
            'messages': messages,
            'stream': True
        }).encode('utf-8')
        req = request.Request(
            f'{self.base_url}/chat/completions',
            data=payload,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        try:
            with request.urlopen(req, timeout=120) as response:
                for raw in response:
                    line = raw.decode('utf-8', errors='replace').strip()
                    if not line.startswith('data:'):
                        continue
                    data = line[5:].strip()
                    if data == '[DONE]':
                        break
                    chunk = json.loads(data)
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    content = delta.get('content')
                    if content:
                        yield content
        except error.URLError as exc:
            raise RuntimeError(f'LLM request failed: {exc}') from exc
```

- [ ] **Step 4: Implement agent loop and SSE packing**

Create `backend/services/agent/loop.py`:

```python
from __future__ import annotations

import json
import os
from pathlib import Path

from .llm import AgentSettings, OpenAICompatibleClient
from .skills import SkillsStore
from .tools import ToolExecutor, parse_tool_blocks


TOOL_DOCS = '''Available tools:
- list_files: {"path":".","depth":1}
- read_file: {"path":"ROADMAP.md"}
- write_file: {"path":"notes/output.md","content":"text"}
- search_files: {"pattern":"FastAPI","path":"."}
- run_shell: {"command":"pwd","timeout":20}
- remember: {"text":"fact to store"}
- recall: {"query":"terms"}
- list_skills: {}
- use_skill: {"name":"project"}
- mcp_list_tools: {}
- mcp_call_tool: {"server":"name","tool":"tool_name","arguments":{}}

Call tools with XML only when needed:
<tool name="read_file">
{"path":"ROADMAP.md"}
</tool>
'''


def default_workspace() -> Path:
    return Path(os.getenv('AGENT_WORKSPACE', Path(__file__).resolve().parents[3])).resolve()


def default_data_dir() -> Path:
    return Path(__file__).resolve().parents[2] / 'data'


def sse_pack(event: str, data: dict) -> str:
    return f'event: {event}\ndata: {json.dumps(data)}\n\n'


def build_system_prompt(memories: list[dict], skills: list[dict]) -> str:
    memory_text = '\n'.join(f'- {item.get("text", "")}' for item in memories[:10]) or '- none'
    skill_text = '\n'.join(f'- {item.get("name")}: {item.get("title")}' for item in skills[:20]) or '- none'
    return f'''You are NAGARE's local agent. Answer clearly and use tools when useful.

{TOOL_DOCS}

Rules:
- Use multiple rounds when tool output changes answer.
- Do not show raw tool XML to the user.
- File paths are relative to workspace.
- Summarize tool results instead of dumping long files.

Memories:
{memory_text}

Skills:
{skill_text}
'''


async def stream_agent(messages: list[dict], settings: AgentSettings | None = None):
    settings = settings or AgentSettings.from_env()
    data_dir = default_data_dir()
    workspace = default_workspace()
    executor = ToolExecutor(workspace=workspace, data_dir=data_dir)
    skills = SkillsStore(data_dir / 'skills').list()
    history = [{'role': 'system', 'content': build_system_prompt(executor.memory.all(), skills)}]
    history.extend(messages)
    client = OpenAICompatibleClient(settings.base_url, settings.api_key)

    for round_index in range(settings.max_rounds):
        full_text = ''
        async for token in client.stream_chat(history, settings.model):
            full_text += token
            yield {'event': 'delta', 'data': {'content': token}}

        visible, calls = parse_tool_blocks(full_text)
        if visible != full_text:
            yield {'event': 'replace_last', 'data': {'content': visible}}
        history.append({'role': 'assistant', 'content': visible})

        if not calls:
            yield {'event': 'done', 'data': {}}
            return

        tool_summaries = []
        for call in calls:
            yield {'event': 'tool_start', 'data': {'name': call.name, 'input': call.arguments}}
            result = executor.execute(call)
            payload = {'name': call.name, 'output': result.output, 'ok': result.ok}
            yield {'event': 'tool_result', 'data': payload}
            tool_summaries.append(f'{call.name} ok={result.ok}\n{result.output}')

        history.append({'role': 'user', 'content': 'Tool results:\n' + '\n\n'.join(tool_summaries)})

    yield {'event': 'error', 'data': {'message': 'agent reached max rounds'}}
    yield {'event': 'done', 'data': {}}
```

- [ ] **Step 5: Run backend checks**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: `5 passed`.

- [ ] **Step 6: Commit task**

```bash
git add backend/services/agent/llm.py backend/services/agent/loop.py backend/tests/test_agent_core.py
git commit -m "feat: add streaming agent loop"
```

---

### Task 3: Basic Stdio MCP Support

**Files:**
- Create: `backend/services/agent/mcp.py`
- Modify: `backend/services/agent/tools.py`
- Create: `backend/data/mcp_servers.json`
- Modify: `backend/tests/test_agent_core.py`

**Interfaces:**
- Produces: `McpConfig(path: Path)`, method `servers() -> dict`.
- Produces: `McpClient(config: McpConfig)`, methods `list_tools() -> dict`, `call_tool(server: str, tool: str, arguments: dict) -> dict`.
- Updates: `ToolExecutor.execute()` supports `mcp_list_tools` and `mcp_call_tool`.

- [ ] **Step 1: Add MCP config checks**

Append to `backend/tests/test_agent_core.py`:

```python
from services.agent.mcp import McpConfig


def test_mcp_config_reads_empty_server_map():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'mcp_servers.json'
        path.write_text('{"servers": {}}', encoding='utf-8')
        config = McpConfig(path)

        assert config.servers() == {}
```

- [ ] **Step 2: Run checks to verify they fail**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: FAIL with import error for `services.agent.mcp`.

- [ ] **Step 3: Implement MCP config and stdio client**

Create `backend/services/agent/mcp.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
import subprocess


class McpConfig:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('{"servers": {}}', encoding='utf-8')

    def servers(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            data = {'servers': {}}
        servers = data.get('servers', {})
        return servers if isinstance(servers, dict) else {}


class McpClient:
    def __init__(self, config: McpConfig):
        self.config = config

    def list_tools(self) -> dict:
        results = {}
        for name in self.config.servers():
            results[name] = self._request(name, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
        return results

    def call_tool(self, server: str, tool: str, arguments: dict) -> dict:
        return self._request(server, {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {'name': tool, 'arguments': arguments}
        })

    def _request(self, server: str, payload: dict) -> dict:
        server_config = self.config.servers().get(server)
        if not server_config:
            return {'error': f'MCP server not configured: {server}'}
        command = [server_config['command'], *server_config.get('args', [])]
        init = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'nagare', 'version': '0.1.0'}}}
        proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            assert proc.stdin is not None
            assert proc.stdout is not None
            proc.stdin.write(json.dumps(init) + '\n')
            proc.stdin.write(json.dumps(payload) + '\n')
            proc.stdin.flush()
            first = proc.stdout.readline()
            second = proc.stdout.readline()
            return json.loads(second or first or '{}')
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
```

- [ ] **Step 4: Add MCP tools to executor**

Modify `backend/services/agent/tools.py` imports:

```python
from .mcp import McpClient, McpConfig
```

Add handlers to `handlers` dictionary in `ToolExecutor.execute`:

```python
            'mcp_list_tools': self._mcp_list_tools,
            'mcp_call_tool': self._mcp_call_tool
```

Add methods to `ToolExecutor`:

```python
    def _mcp_client(self) -> McpClient:
        return McpClient(McpConfig(self.data_dir / 'mcp_servers.json'))

    def _mcp_list_tools(self, args: dict) -> ToolResult:
        return ToolResult(True, json.dumps(self._mcp_client().list_tools(), indent=2))

    def _mcp_call_tool(self, args: dict) -> ToolResult:
        server = str(args.get('server', ''))
        tool = str(args.get('tool', ''))
        arguments = args.get('arguments', {})
        if not server or not tool:
            return ToolResult(False, 'server and tool required')
        if not isinstance(arguments, dict):
            return ToolResult(False, 'arguments must be object')
        return ToolResult(True, json.dumps(self._mcp_client().call_tool(server, tool, arguments), indent=2))
```

- [ ] **Step 5: Create default MCP config**

Create `backend/data/mcp_servers.json`:

```json
{
  "servers": {}
}
```

- [ ] **Step 6: Run backend checks**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: `6 passed`.

- [ ] **Step 7: Commit task**

```bash
git add backend/services/agent/mcp.py backend/services/agent/tools.py backend/data/mcp_servers.json backend/tests/test_agent_core.py
git commit -m "feat: add basic mcp tool bridge"
```

---

### Task 4: FastAPI Chat Streaming Router

**Files:**
- Create: `backend/routers/chat.py`
- Modify: `backend/main.py`

**Interfaces:**
- Consumes: `stream_agent(messages, settings)` and `sse_pack(event, data)` from Task 2.
- Produces: `POST /api/chat/stream` SSE endpoint.

- [ ] **Step 1: Create chat router**

Create `backend/routers/chat.py`:

```python
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.agent.llm import AgentSettings
from services.agent.loop import sse_pack, stream_agent


router = APIRouter(prefix='/api/chat', tags=['chat'])


class ChatMessage(BaseModel):
    role: Literal['user', 'assistant', 'system']
    content: str = Field(min_length=1)


class ToolFlags(BaseModel):
    files: bool = True
    shell: bool = True
    mcp: bool = True


class ChatStreamRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    tools: ToolFlags = Field(default_factory=ToolFlags)
    max_rounds: int | None = Field(default=None, ge=1, le=20)


async def event_stream(payload: ChatStreamRequest) -> AsyncIterator[str]:
    settings = AgentSettings.from_env()
    if payload.model:
        settings = AgentSettings(settings.base_url, settings.api_key, payload.model, settings.max_rounds)
    if payload.max_rounds:
        settings = AgentSettings(settings.base_url, settings.api_key, settings.model, payload.max_rounds)
    try:
        messages = [message.model_dump() for message in payload.messages]
        async for item in stream_agent(messages, settings):
            yield sse_pack(item['event'], item['data'])
    except Exception as exc:
        yield sse_pack('error', {'message': str(exc)})
        yield sse_pack('done', {})


@router.post('/stream')
async def chat_stream(payload: ChatStreamRequest):
    return StreamingResponse(event_stream(payload), media_type='text/event-stream')
```

- [ ] **Step 2: Wire router in FastAPI app**

Modify `backend/main.py` import:

```python
from routers import evaluations, agents, datasets, monitoring, logs, chat
```

Add after existing router includes:

```python
app.include_router(chat.router)
```

- [ ] **Step 3: Run backend checks**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: all tests pass.

Run import smoke from `backend`:

```bash
python -c "from main import app; print(app.title)"
```

Expected: `NAGARE OS API`.

- [ ] **Step 4: Commit task**

```bash
git add backend/routers/chat.py backend/main.py
git commit -m "feat: expose chat streaming api"
```

---

### Task 5: Nuxt Chat SSE Client and Tool UI

**Files:**
- Modify: `frontend/app/components/chat/ChatView.vue`

**Interfaces:**
- Consumes: `POST ${apiBase}/api/chat/stream` SSE events: `delta`, `replace_last`, `tool_start`, `tool_result`, `error`, `done`.
- Produces: chat page with real streaming assistant and tool event rendering.

- [ ] **Step 1: Replace script block**

In `frontend/app/components/chat/ChatView.vue`, replace the entire `<script setup lang="ts">...</script>` block with:

```vue
<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Waves, ArrowUp, FileText, User, Wrench } from '@lucide/vue'

interface ToolEvent {
  id: string
  name: string
  input?: unknown
  output?: string
  error?: string
  status: 'running' | 'done' | 'error'
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
  toolEvents?: ToolEvent[]
}

const route = useRoute()
const config = useRuntimeConfig()
const messages = ref<Message[]>([])
const input = ref('')
const busy = ref(false)
const scrollRef = ref<HTMLDivElement | null>(null)
const seededRef = ref(false)
const errorText = ref('')

const scrollToBottom = () => {
  nextTick(() => {
    scrollRef.value?.scrollTo({
      top: scrollRef.value.scrollHeight,
      behavior: 'smooth'
    })
  })
}

const updateAssistant = (id: string, patch: Partial<Message>) => {
  messages.value = messages.value.map((message) => message.id === id ? { ...message, ...patch } : message)
}

const addToolEvent = (assistantId: string, event: ToolEvent) => {
  messages.value = messages.value.map((message) => {
    if (message.id !== assistantId) return message
    return { ...message, toolEvents: [...(message.toolEvents || []), event] }
  })
}

const finishToolEvent = (assistantId: string, name: string, output: string, ok = true) => {
  messages.value = messages.value.map((message) => {
    if (message.id !== assistantId) return message
    const toolEvents = (message.toolEvents || []).map((event) => {
      if (event.name === name && event.status === 'running') {
        return { ...event, output, status: ok ? 'done' as const : 'error' as const }
      }
      return event
    })
    return { ...message, toolEvents }
  })
}

const parseSse = (buffer: string) => {
  const parts = buffer.split('\n\n')
  const rest = parts.pop() || ''
  const events = parts.map((part) => {
    const eventLine = part.split('\n').find((line) => line.startsWith('event: '))
    const dataLine = part.split('\n').find((line) => line.startsWith('data: '))
    return {
      event: eventLine?.slice(7) || 'message',
      data: dataLine ? JSON.parse(dataLine.slice(6)) : {}
    }
  })
  return { events, rest }
}

const send = async (text: string) => {
  const trimmed = text.trim()
  if (!trimmed || busy.value) return

  errorText.value = ''
  const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: trimmed }
  const assistantId = crypto.randomUUID()
  messages.value.push(userMsg, { id: assistantId, role: 'assistant', content: '', streaming: true, toolEvents: [] })
  input.value = ''
  busy.value = true
  scrollToBottom()

  try {
    const response = await fetch(`${config.public.apiBase}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: messages.value
          .filter((message) => message.role === 'user' || (message.role === 'assistant' && message.content.trim()))
          .map((message) => ({ role: message.role, content: message.content })),
        max_rounds: 8
      })
    })

    if (!response.ok || !response.body) throw new Error(`Chat request failed: ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parsed = parseSse(buffer)
      buffer = parsed.rest

      for (const item of parsed.events) {
        if (item.event === 'delta') {
          const current = messages.value.find((message) => message.id === assistantId)
          updateAssistant(assistantId, { content: `${current?.content || ''}${item.data.content || ''}` })
        } else if (item.event === 'replace_last') {
          updateAssistant(assistantId, { content: item.data.content || '' })
        } else if (item.event === 'tool_start') {
          addToolEvent(assistantId, {
            id: crypto.randomUUID(),
            name: item.data.name,
            input: item.data.input,
            status: 'running'
          })
        } else if (item.event === 'tool_result') {
          finishToolEvent(assistantId, item.data.name, item.data.output || '', item.data.ok !== false)
        } else if (item.event === 'error') {
          errorText.value = item.data.message || 'Agent failed'
          updateAssistant(assistantId, { content: errorText.value })
        } else if (item.event === 'done') {
          updateAssistant(assistantId, { streaming: false })
          busy.value = false
        }
        scrollToBottom()
      }
    }
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : 'Chat request failed'
    updateAssistant(assistantId, { content: errorText.value, streaming: false })
    busy.value = false
  }
}

onMounted(() => {
  if (seededRef.value) return
  seededRef.value = true
  const q = typeof route.query.q === 'string' ? route.query.q : ''
  if (q) send(q)
})

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    if (e.isComposing) return
    e.preventDefault()
    send(input.value)
  }
}

const empty = computed(() => messages.value.length === 0)
</script>
```

- [ ] **Step 2: Remove source-card markup and add tool events block**

In assistant message content area, keep message text and add this block below it:

```vue
<div
  v-if="m.toolEvents && m.toolEvents.length > 0"
  class="mt-4 space-y-2"
>
  <div class="text-[11px] font-semibold uppercase tracking-wider text-stone-400 mb-2">
    Tool activity
  </div>
  <div
    v-for="tool in m.toolEvents"
    :key="tool.id"
    class="rounded-xl border border-stone-200 bg-white p-3 text-xs text-stone-600"
  >
    <div class="flex items-center justify-between gap-2 mb-1">
      <span class="flex items-center gap-1.5 font-semibold text-stone-700">
        <Wrench :size="13" />
        {{ tool.name }}
      </span>
      <span
        class="text-[10px] font-semibold uppercase"
        :class="tool.status === 'error' ? 'text-red-600' : tool.status === 'done' ? 'text-emerald-600' : 'text-blue-600'"
      >
        {{ tool.status }}
      </span>
    </div>
    <pre v-if="tool.output" class="max-h-32 overflow-auto whitespace-pre-wrap rounded-lg bg-stone-50 p-2">{{ tool.output }}</pre>
  </div>
</div>
```

Also remove `sources?: Source[]`, `mockReply`, and all `Source` imports/usages from the file.

- [ ] **Step 3: Run frontend typecheck**

Run from `frontend`:

```bash
pnpm typecheck
```

Expected: command exits `0`.

- [ ] **Step 4: Commit task**

```bash
git add frontend/app/components/chat/ChatView.vue
git commit -m "feat: wire chat ui to streaming agent"
```

---

### Task 6: End-to-End Smoke and Final Fixes

**Files:**
- Modify only files from prior tasks if checks expose concrete bugs.

**Interfaces:**
- Consumes: backend router, agent loop, frontend SSE client.
- Produces: verified feature with command output recorded in final response.

- [ ] **Step 1: Run backend checks**

Run from `backend`:

```bash
python -m pytest tests/test_agent_core.py -q
```

Expected: all tests pass.

- [ ] **Step 2: Run FastAPI import smoke**

Run from `backend`:

```bash
python -c "from main import app; print([route.path for route in app.routes if route.path == '/api/chat/stream'])"
```

Expected:

```text
['/api/chat/stream']
```

- [ ] **Step 3: Run frontend typecheck**

Run from `frontend`:

```bash
pnpm typecheck
```

Expected: exits `0`.

- [ ] **Step 4: Start backend manually for smoke**

Run from `backend`:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

Expected: backend starts and logs Uvicorn running on `http://127.0.0.1:8000`.

- [ ] **Step 5: Start frontend manually for smoke**

Run from `frontend`:

```bash
pnpm dev
```

Expected: Nuxt starts and prints local URL, usually `http://localhost:3000`.

- [ ] **Step 6: Manual chat smoke**

Open `/chat` and send:

```text
List files, read ROADMAP.md, remember project goal, then summarize.
```

Expected:

- Assistant text streams.
- Tool activity panel shows `list_files`, `read_file`, and `remember` if model follows tool prompt.
- If no local LLM is running, UI displays `LLM request failed` inline and recovers.

- [ ] **Step 7: Commit verification fixes**

If Step 1-6 required changes:

```bash
git add backend frontend
git commit -m "fix: stabilize streaming chat agent"
```

If no changes:

```bash
git status --short
```

Expected: no unexpected tracked changes beyond completed commits.

---

## Self-Review

- Spec coverage: backend SSE endpoint in Task 4; OpenAI-compatible LLM in Task 2; multi-round XML tool loop in Task 2; file/shell tools in Task 1; JSON memory in Task 1; Markdown skills in Task 1; basic stdio MCP in Task 3; Nuxt SSE frontend in Task 5; checks in Tasks 1, 2, 3, and 6.
- Type consistency: `ToolCall`, `ToolResult`, `ToolExecutor`, `AgentSettings`, `stream_agent`, `sse_pack`, and SSE event names are defined before downstream use.
- Scope check: one vertical slice, no DB/auth/vector memory/native tool-calling work included.
