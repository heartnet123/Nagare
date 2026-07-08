from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Literal, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.agent.llm import AgentSettings
from services.agent.loop import sse_pack, stream_agent
from services.session_manager import SessionManager

router = APIRouter(prefix='/api/chat', tags=['chat'])

# SessionManager injected at startup by main.py
_session_manager: SessionManager | None = None


def _register(sm: SessionManager):
    global _session_manager
    _session_manager = sm


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
    session_id: str | None = None


async def event_stream(payload: ChatStreamRequest) -> AsyncIterator[str]:
    settings = AgentSettings.from_config_file()
    if payload.model:
        settings = AgentSettings(settings.base_url, settings.api_key, payload.model, settings.max_rounds)
    if payload.max_rounds:
        settings = AgentSettings(settings.base_url, settings.api_key, settings.model, payload.max_rounds)

    sm = _session_manager
    session_mode = None
    if sm and payload.session_id:
        try:
            session = None
            try:
                session = sm.get_session(payload.session_id)
            except KeyError:
                session = sm.create_session(
                    session_id=payload.session_id,
                    name="New Chat",
                    model=payload.model or settings.model,
                    endpoint_url=settings.base_url,
                )
            if session:
                session_mode = session.get("mode")
            last_user = next((msg for msg in reversed(payload.messages) if msg.role == 'user'), None)
            existing_messages = session.get("messages", []) if session else []
            last_saved = existing_messages[-1] if existing_messages else None
            if last_user and (
                not last_saved
                or last_saved.get("role") != "user"
                or last_saved.get("content") != last_user.content
            ):
                sm.add_message(payload.session_id, 'user', last_user.content, metadata={"source": "user"})
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist user message: {exc}")

    is_chat_mode = (session_mode == 'chat')
    if is_chat_mode:
        settings = AgentSettings(settings.base_url, settings.api_key, settings.model, 1)

    assistant_buffer = ''
    try:
        messages = [message.model_dump() for message in payload.messages]
        async for item in stream_agent(messages, settings, tools=not is_chat_mode):
            event = item['event']
            data = item['data']

            if event == 'delta':
                assistant_buffer += data.get('content', '')
            elif event == 'replace_last':
                assistant_buffer = data.get('content', '')

            yield sse_pack(event, data)

            if sm and payload.session_id:
                try:
                    if event == 'tool_start':
                        sm.add_message(
                            payload.session_id,
                            'assistant',
                            f"🛠 **{data.get('name', 'tool')}**",
                            metadata={"tool_call": data.get('name'), "tool_input": data.get('input'), "source": "tool"},
                        )
                    elif event == 'tool_result':
                        sm.add_message(
                            payload.session_id,
                            'user',
                            f"_Tool result for `{data.get('name', 'tool')}`:_\n{data.get('output', '')}",
                            metadata={"tool_result": data.get('name'), "ok": data.get('ok'), "source": "tool"},
                        )
                except Exception as exc:
                    import logging
                    logging.getLogger(__name__).warning(f"Failed to persist tool message: {exc}")

    except Exception as exc:
        yield sse_pack('error', {'message': str(exc)})
        yield sse_pack('done', {})

    if sm and payload.session_id and assistant_buffer.strip():
        try:
            sm.add_message(
                payload.session_id,
                'assistant',
                assistant_buffer,
                metadata={"model": settings.model, "source": "assistant"},
            )
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist assistant message: {exc}")


class RegenerateRequest(BaseModel):
    session_id: str
    model: str | None = None
    max_rounds: int | None = Field(default=None, ge=1, le=20)


@router.post('/stream')
async def chat_stream(payload: ChatStreamRequest):
    return StreamingResponse(event_stream(payload), media_type='text/event-stream')


@router.post('/regenerate')
async def chat_regenerate(payload: RegenerateRequest):
    sm = _session_manager
    if not sm:
        from fastapi import HTTPException
        raise HTTPException(503, "Session manager not initialized")

    try:
        messages = sm.get_messages(payload.session_id)
    except KeyError:
        from fastapi import HTTPException
        raise HTTPException(404, f"Session '{payload.session_id}' not found")

    if not messages:
        from fastapi import HTTPException
        raise HTTPException(400, "No message history to regenerate")

    # Find last user message index
    last_user_idx = -1
    for idx, msg in enumerate(messages):
        # We check metadata source to make sure we don't treat tool output as user message
        if msg['role'] == 'user' and msg.get('metadata', {}).get('source') == 'user':
            last_user_idx = idx

    if last_user_idx == -1:
        # Fallback to any user role message
        for idx, msg in enumerate(messages):
            if msg['role'] == 'user':
                last_user_idx = idx

    if last_user_idx == -1:
        from fastapi import HTTPException
        raise HTTPException(400, "No user message found to regenerate from")

    # Keep history up to that user message
    cleaned = messages[:last_user_idx + 1]

    # Persist the cleaned messages list
    sm.replace_messages(payload.session_id, cleaned)

    # Map to ChatMessage Pydantic list
    chat_messages = []
    for m in cleaned:
        chat_messages.append(ChatMessage(role=m['role'], content=m['content']))

    stream_payload = ChatStreamRequest(
        messages=chat_messages,
        model=payload.model,
        max_rounds=payload.max_rounds,
        session_id=payload.session_id
    )
    return StreamingResponse(event_stream(stream_payload), media_type='text/event-stream')
