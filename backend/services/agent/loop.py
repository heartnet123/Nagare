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
