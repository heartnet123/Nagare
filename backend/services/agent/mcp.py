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
