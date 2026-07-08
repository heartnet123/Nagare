import pytest
from pathlib import Path
import tempfile

from services.agent.mcp import McpConfig
from routers import mcp
from routers.mcp import (
    McpServerCreate,
    McpServerUpdate,
    list_servers,
    create_server,
    update_server,
    delete_server
)


@pytest.fixture(autouse=True)
def temp_mcp_config(monkeypatch):
    """Fixture to mock MCP configuration file path in routers.mcp."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / 'mcp_servers.json'
        config_path.write_text('{"servers": {}}', encoding='utf-8')
        
        # Monkeypatch the get_mcp_config function to return a temp config
        monkeypatch.setattr(mcp, 'get_mcp_config', lambda: McpConfig(config_path))
        yield config_path


@pytest.mark.anyio
async def test_list_servers_initially_empty():
    servers = await list_servers()
    assert servers == []


@pytest.mark.anyio
async def test_create_and_read_server():
    # Create server
    payload = McpServerCreate(
        name='test-server',
        command='node',
        args=['test.js']
    )
    res = await create_server(payload)
    assert res.name == 'test-server'
    assert res.command == 'node'
    assert res.args == ['test.js']
    
    # Verify in list
    servers = await list_servers()
    assert len(servers) == 1
    assert servers[0].name == 'test-server'


@pytest.mark.anyio
async def test_create_duplicate_server_fails():
    payload = McpServerCreate(
        name='test-server',
        command='node',
        args=['test.js']
    )
    await create_server(payload)
    
    # Create duplicate
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await create_server(payload)
    assert exc.value.status_code == 400
    assert "already exists" in exc.value.detail


@pytest.mark.anyio
async def test_update_server():
    # Pre-populate
    payload = McpServerCreate(
        name='test-server',
        command='node',
        args=['test.js']
    )
    await create_server(payload)
    
    # Update
    update_payload = McpServerUpdate(
        command='python',
        args=['script.py']
    )
    res = await update_server('test-server', update_payload)
    assert res.name == 'test-server'
    assert res.command == 'python'
    assert res.args == ['script.py']


@pytest.mark.anyio
async def test_update_nonexistent_server_fails():
    update_payload = McpServerUpdate(
        command='python',
        args=['script.py']
    )
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await update_server('non-existent', update_payload)
    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_delete_server():
    # Pre-populate
    payload = McpServerCreate(
        name='test-server',
        command='node',
        args=['test.js']
    )
    await create_server(payload)
    
    # Delete
    await delete_server('test-server')
    
    # Verify empty
    servers = await list_servers()
    assert servers == []


@pytest.mark.anyio
async def test_delete_nonexistent_server_fails():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        await delete_server('non-existent')
    assert exc.value.status_code == 404
