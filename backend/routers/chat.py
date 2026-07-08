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
    settings = AgentSettings.from_config_file()
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
