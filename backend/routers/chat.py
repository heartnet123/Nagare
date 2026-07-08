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
    if sm and payload.session_id:
        try:
            try:
                sm.get_session(payload.session_id)
            except KeyError:
                sm.create_session(
                    session_id=payload.session_id,
                    name="New Chat",
                    model=payload.model or settings.model,
                    endpoint_url=settings.base_url,
                )
            for msg in payload.messages:
                if msg.role == 'user':
                    sm.add_message(payload.session_id, msg.role, msg.content, metadata={"source": "user"})
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f"Failed to persist user message: {exc}")

    assistant_buffer = ''
    try:
        messages = [message.model_dump() for message in payload.messages]
        async for item in stream_agent(messages, settings):
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


@router.post('/stream')
async def chat_stream(payload: ChatStreamRequest):
    return StreamingResponse(event_stream(payload), media_type='text/event-stream')
