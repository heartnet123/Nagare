# Chat + Agents Streaming — Design

**Project:** NAGARE OS  
**Feature:** Chat + Agents streaming vertical slice  
**Date:** 2026-07-07  
**Status:** Approved design draft

## Goal

Replace mock chat with a working frontend + backend + AI path. Add a small Odysseus-inspired agent loop with streaming, multi-round tool execution, files, shell, skills, memory, and basic MCP support.

## Scope

### Included

- FastAPI `/api/chat/stream` Server-Sent Events endpoint.
- OpenAI-compatible LLM backend using environment variables.
- Multi-round text tool-call loop.
- Safe file tools confined to a workspace root.
- Shell tool with timeout and destructive-command denylist.
- JSON memory store.
- Markdown skills store.
- Basic stdio MCP tool listing/calling.
- Nuxt chat page wired to real SSE stream.
- Tool activity rendering in chat UI.
- One backend runnable check for parser/tools/memory.
- Frontend typecheck.

### Not Included

- Auth, DB persistence, multi-user ownership.
- Full Odysseus module transplant.
- Native OpenAI function calling.
- Remote HTTP/SSE MCP transports.
- Long-term vector memory.
- File upload UI.

## Backend Design

Add bounded agent package:

```text
backend/
  routers/chat.py
  services/agent/
    __init__.py
    loop.py
    llm.py
    tools.py
    memory.py
    skills.py
    mcp.py
```

Wire `routers.chat.router` in `backend/main.py`.

### Endpoint

`POST /api/chat/stream`

Request body:

```json
{
  "messages": [{ "role": "user", "content": "hello" }],
  "model": "optional model override",
  "tools": { "files": true, "shell": true, "mcp": true },
  "max_rounds": 8
}
```

Response uses SSE:

```text
event: delta
data: {"content":"text"}

event: tool_start
data: {"name":"read_file","input":{"path":"README.md"}}

event: tool_result
data: {"name":"read_file","output":"..."}

event: error
data: {"message":"..."}

event: done
data: {}
```

## Agent Loop

Use OpenAI-compatible chat completions.

Environment:

- `AGENT_OPENAI_BASE_URL` default `http://localhost:11434/v1`
- `AGENT_OPENAI_API_KEY` default `ollama`
- `AGENT_MODEL` default `llama3.1`
- `AGENT_WORKSPACE` default project root
- `AGENT_MAX_ROUNDS` default `8`

Tool-call protocol uses XML blocks so any chat model can emit calls:

```xml
<tool name="read_file">
{"path":"README.md"}
</tool>
```

Loop steps:

1. Build system prompt with rules, tool docs, memories, and skills.
2. Stream assistant text from LLM.
3. Parse tool blocks from assistant output.
4. Execute each tool.
5. Append tool results as context.
6. Continue until no tool block or `max_rounds` reached.

Frontend receives all assistant text as deltas. Tool XML may be withheld from final display by stripping parsed tool blocks from assistant text before final message state.

## Tools

Minimum tool set:

| Tool | Purpose |
|---|---|
| `list_files` | List workspace files/directories. |
| `read_file` | Read UTF-8 text file in workspace. |
| `write_file` | Write UTF-8 text file in workspace. |
| `search_files` | Regex search workspace files. |
| `run_shell` | Run shell command with timeout. |
| `remember` | Save memory item. |
| `recall` | Search memory items. |
| `list_skills` | List local skill files. |
| `use_skill` | Read one skill file. |
| `mcp_list_tools` | List tools from configured MCP servers. |
| `mcp_call_tool` | Call configured MCP server tool. |

### Security

File tools:

- Resolve paths with `Path.resolve()`.
- Reject paths outside `AGENT_WORKSPACE`.
- Reject binary decode errors with clear tool error.

Shell tool:

- Use timeout, default 20 seconds.
- Run in workspace.
- Deny obvious destructive commands: `rm -rf`, `del /s`, `format`, `shutdown`, fork bombs.
- Return stdout, stderr, exit code.

MCP:

- Read config from `backend/data/mcp_servers.json`.
- Support stdio command + args only.
- Spawn per operation; no long-lived process manager in first slice.
- JSON-RPC `initialize`, `tools/list`, `tools/call` only.

## Memory and Skills

Storage:

```text
backend/data/agent_memory.json
backend/data/skills/*.md
backend/data/mcp_servers.json
```

Memory schema:

```json
[
  { "id": "uuid", "text": "...", "created_at": "ISO-8601" }
]
```

Skills are Markdown files. `list_skills` returns filename + first heading. `use_skill` returns content.

## Frontend Design

Modify `frontend/app/components/chat/ChatView.vue`:

- Remove `mockReply` streaming timer.
- Send POST to `${runtimeConfig.public.apiBase}/api/chat/stream`.
- Parse SSE from `response.body.getReader()`.
- Append assistant deltas to current assistant message.
- Render tool events under assistant response.
- Show inline error if endpoint/LLM fails.
- Keep `?q=` auto-send behavior.

Message shape:

```ts
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
```

## Error Handling

- Endpoint emits `error` SSE before `done` when recoverable.
- Tool failures return tool result text; loop continues unless all rounds exhausted.
- LLM connection failure displays frontend inline error and ends assistant streaming state.
- Invalid requests return FastAPI validation errors.

## Verification

Backend:

- Add assert-based check for:
  - XML tool parser.
  - workspace sandbox rejects `..` escape.
  - memory save + recall.

Frontend:

- Run `pnpm typecheck` in `frontend`.

Manual smoke:

1. Set `AGENT_OPENAI_BASE_URL`, `AGENT_OPENAI_API_KEY`, `AGENT_MODEL`.
2. Start backend with `uvicorn main:app --reload` from `backend`.
3. Start frontend with `pnpm dev` from `frontend`.
4. Open `/chat`.
5. Ask: `List files, read ROADMAP.md, remember project goal, then summarize.`
6. Confirm deltas stream and tool events appear.

## Acceptance Criteria

- Chat page uses real backend stream, not mock reply.
- Assistant text streams incrementally.
- Agent can perform at least two tool rounds in one response.
- File read/list/search work inside workspace only.
- Shell tool returns stdout/stderr/exit code and times out.
- Memory save/recall work across backend restarts.
- Skills list/read works with Markdown files.
- MCP config file exists and stdio list/call path is implemented.
- Backend runnable check passes.
- Frontend typecheck passes.

## Deliberate Simplifications

- `ponytail:` JSON memory instead of DB. Ceiling: single-user local state. Upgrade to DB after auth lands.
- `ponytail:` XML tool protocol instead of native tool calling. Ceiling: works across models but less structured. Upgrade when provider abstraction stabilizes.
- `ponytail:` per-call MCP process. Ceiling: slower MCP calls. Upgrade to managed persistent sessions when more MCP usage exists.
