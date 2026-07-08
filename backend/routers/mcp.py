from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.agent.mcp import McpConfig

router = APIRouter(prefix='/api/mcp', tags=['mcp'])


class McpServerCreate(BaseModel):
    name: str = Field(min_length=1, pattern=r'^[a-zA-Z0-9_\-]+$')
    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)


class McpServerUpdate(BaseModel):
    command: str = Field(min_length=1)
    args: list[str] = Field(default_factory=list)


class McpServerResponse(BaseModel):
    name: str
    command: str
    args: list[str]


def get_mcp_config() -> McpConfig:
    data_dir = Path(__file__).resolve().parents[1] / 'data'
    return McpConfig(data_dir / 'mcp_servers.json')


@router.get('/servers', response_model=list[McpServerResponse])
async def list_servers():
    """List all custom MCP servers."""
    config = get_mcp_config()
    servers = config.servers()
    return [
        McpServerResponse(name=name, command=info['command'], args=info.get('args', []))
        for name, info in servers.items()
    ]


@router.post('/servers', response_model=McpServerResponse, status_code=201)
async def create_server(payload: McpServerCreate):
    """Add a new custom MCP server configuration."""
    config = get_mcp_config()
    servers = config.servers()

    if payload.name in servers:
        raise HTTPException(status_code=400, detail=f"MCP server '{payload.name}' already exists.")

    servers[payload.name] = {
        'command': payload.command,
        'args': payload.args
    }
    config.save(servers)

    return McpServerResponse(name=payload.name, command=payload.command, args=payload.args)


@router.put('/servers/{name}', response_model=McpServerResponse)
async def update_server(name: str, payload: McpServerUpdate):
    """Update an existing MCP server configuration."""
    config = get_mcp_config()
    servers = config.servers()

    if name not in servers:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found.")

    servers[name] = {
        'command': payload.command,
        'args': payload.args
    }
    config.save(servers)

    return McpServerResponse(name=name, command=payload.command, args=payload.args)


@router.delete('/servers/{name}', status_code=204)
async def delete_server(name: str):
    """Delete an MCP server configuration."""
    config = get_mcp_config()
    servers = config.servers()

    if name not in servers:
        raise HTTPException(status_code=404, detail=f"MCP server '{name}' not found.")

    del servers[name]
    config.save(servers)
