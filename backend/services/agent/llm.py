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
