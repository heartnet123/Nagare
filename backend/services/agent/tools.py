from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import subprocess

from .memory import MemoryStore
from .skills import SkillsStore
from .mcp import McpClient, McpConfig
from services.memory import MemoryService


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
        self.memory_svc = MemoryService(data_dir)
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
            'use_skill': self._use_skill,
            'mcp_list_tools': self._mcp_list_tools,
            'mcp_call_tool': self._mcp_call_tool
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
        # Use MemoryService for enriched storage (category, source, pinned)
        entry = self.memory_svc.manager.add_entry(text, source="agent")
        memories = self.memory_svc.manager.load_all()
        memories.append(entry)
        self.memory_svc.manager.save(memories)
        # Also add to vector store if available
        if self.memory_svc.vector_store and self.memory_svc.vector_store.healthy:
            self.memory_svc.vector_store.add(entry["id"], text)
        # Keep the old MemoryStore in sync for backward compat
        self.memory.add(text)
        return ToolResult(True, json.dumps(entry))

    def _recall(self, args: dict) -> ToolResult:
        query = str(args.get('query', ''))
        # Use MemoryService for keyword + Jaccard relevance scoring
        memories = self.memory_svc.manager.get_relevant_memories(query, max_items=10)
        if memories:
            return ToolResult(True, json.dumps(memories, indent=2))
        # Fallback to old MemoryStore search
        return ToolResult(True, json.dumps(self.memory.search(query), indent=2))

    def _list_skills(self, args: dict) -> ToolResult:
        return ToolResult(True, json.dumps(self.skills.list(), indent=2))

    def _use_skill(self, args: dict) -> ToolResult:
        name = str(args.get('name', ''))
        if not name:
            return ToolResult(False, 'name required')
        return ToolResult(True, self.skills.read(name))

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

