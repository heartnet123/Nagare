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
- search_knowledge: {"query":"query string","limit":5}

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


def build_system_prompt(memories: list[dict], skills: list[dict], system_prompt_append: str = '', tools: bool = True) -> str:
    # Show pinned memories first, then by recency
    pinned = [m for m in memories if m.get('pinned')]
    rest = [m for m in memories if not m.get('pinned')]
    ordered = sorted(pinned, key=lambda m: m.get('timestamp', 0), reverse=True)
    ordered += sorted(rest, key=lambda m: m.get('timestamp', 0), reverse=True)

    memory_lines = []
    for item in ordered[:10]:
        cat = item.get('category', '')
        text = item.get('text', '')
        if cat and cat != 'fact':
            memory_lines.append(f'- [{cat}] {text}')
        else:
            memory_lines.append(f'- {text}')
    memory_text = '\n'.join(memory_lines) or '- none'

    skill_text = '\n'.join(f'- {item.get("name")}: {item.get("title")}' for item in skills[:20]) or '- none'
    if tools:
        base = f'''You are NAGARE's local agent. Answer clearly and use tools when useful.

{TOOL_DOCS}

Rules:
- Use multiple rounds when tool output changes answer.
- Do not show raw tool XML to the user.
- File paths are relative to workspace.
- Summarize tool results instead of dumping long files.
- When the user asks about uploaded documents, a knowledge base, files, or facts, use search_knowledge first to query context.
- Always cite sources for facts retrieved from the knowledge base using the format [Source: filename, page N] or [Source: filename].
- Provide a confidence score or statement if the RAG search results have low/high confidence.

Memories:
{memory_text}

Skills:
{skill_text}
'''
    else:
        base = f'''You are NAGARE's local agent. Answer clearly.

Rules:
- File paths are relative to workspace.
- When the user asks about uploaded documents, a knowledge base, files, or facts, cite sources using the format [Source: filename, page N] or [Source: filename].

Memories:
{memory_text}

Skills:
{skill_text}
'''
    if system_prompt_append and system_prompt_append.strip():
        base = base.rstrip() + '\n\n' + system_prompt_append.strip() + '\n'
    return base


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    import tiktoken
    try:
        encoding = tiktoken.encoding_for_model(model)
    except Exception:
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            return len(text) // 4  # fallback rough estimate
    return len(encoding.encode(text))


async def stream_agent(messages: list[dict], settings: AgentSettings | None = None, tools: bool = True):
    import time
    start_time = time.time()
    
    settings = settings or AgentSettings.from_config_file()
    data_dir = default_data_dir()
    workspace = default_workspace()
    # Load system_prompt_append from persisted config if present
    _system_prompt_append = ''
    try:
        import json as _json
        _cfg_path = data_dir / 'agent_config.json'
        if _cfg_path.exists():
            _system_prompt_append = _json.loads(_cfg_path.read_text('utf-8')).get('system_prompt_append', '')
    except Exception:
        pass
    executor = ToolExecutor(workspace=workspace, data_dir=data_dir)
    skills = SkillsStore(data_dir / 'skills').list()
    
    system_prompt = build_system_prompt(executor.memory_svc.manager.load_all(), skills, _system_prompt_append, tools=tools)
    history = [{'role': 'system', 'content': system_prompt}]
    history.extend(messages)
    
    # Calculate input tokens
    input_text = system_prompt + "\n" + "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)
    input_tokens = count_tokens(input_text, settings.model)
    
    client = OpenAICompatibleClient(settings.base_url, settings.api_key)

    total_output_tokens = 0
    full_text = ''
    
    for round_index in range(settings.max_rounds):
        round_text = ''
        async for token in client.stream_chat(history, settings.model):
            round_text += token
            full_text += token
            yield {'event': 'delta', 'data': {'content': token}}

        visible, calls = parse_tool_blocks(round_text)
        if visible != round_text:
            yield {'event': 'replace_last', 'data': {'content': visible}}
        history.append({'role': 'assistant', 'content': visible})

        if not calls or not tools:
            elapsed_ms = int((time.time() - start_time) * 1000)
            output_tokens = count_tokens(full_text, settings.model)
            yield {'event': 'done', 'data': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'response_time_ms': elapsed_ms
            }}
            return

        tool_summaries = []
        for call in calls:
            yield {'event': 'tool_start', 'data': {'name': call.name, 'input': call.arguments}}
            result = executor.execute(call)
            payload = {'name': call.name, 'output': result.output, 'ok': result.ok}
            yield {'event': 'tool_result', 'data': payload}
            tool_summaries.append(f'{call.name} ok={result.ok}\n{result.output}')

        history.append({'role': 'user', 'content': 'Tool results:\n' + '\n\n'.join(tool_summaries)})

    elapsed_ms = int((time.time() - start_time) * 1000)
    output_tokens = count_tokens(full_text, settings.model)
    yield {'event': 'error', 'data': {'message': 'agent reached max rounds'}}
    yield {'event': 'done', 'data': {
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'response_time_ms': elapsed_ms
    }}

