from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import agents as agents_router
from services.data import connect_db, init_db


@pytest.fixture()
def agents_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    test_user_id = str(uuid4())

    def connect_temp_db() -> sqlite3.Connection:
        conn = connect_db(tmp_path)
        # Ensure user exists for foreign key
        conn.execute(
            "INSERT OR IGNORE INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (test_user_id, "testuser", "fakehash", "2025-01-01T00:00:00Z"),
        )
        conn.commit()
        return conn

    async def mock_current_user():
        return {"id": test_user_id, "username": "testuser"}

    monkeypatch.setattr(agents_router, "connect_db", connect_temp_db)

    app = FastAPI()
    app.dependency_overrides[agents_router.get_current_user_from_cookie] = mock_current_user
    app.include_router(agents_router.router)
    return TestClient(app)


def test_list_agents_empty(agents_client: TestClient):
    res = agents_client.get("/api/agents")
    assert res.status_code == 200
    assert res.json() == []


def test_create_and_get_agent(agents_client: TestClient):
    payload = {
        "name": "Atlas",
        "role_title": "Research agent",
        "category": "Research",
        "description": "Find and synthesize info",
        "tags": ["Web research", "Reports"],
        "uses_count": 1200,
        "completion_rate": 96,
        "model": "llama3.1",
        "system_prompt": "You are a research agent",
        "skills": ["project"],
        "type": "search",
        "status": "active",
        "capabilities": ["Search web"],
        "tools": ["Search", "Notion"],
        "recent_wins": [{"title": "Report", "time": "4m", "date": "Apr 27"}],
    }
    create_res = agents_client.post("/api/agents", json=payload)
    assert create_res.status_code == 201
    created = create_res.json()
    assert created["name"] == "Atlas"
    assert created["role_title"] == "Research agent"
    assert created["uses_count"] == 1200
    assert created["completion_rate"] == 96
    assert "Search" in created["tools"]

    agent_id = created["id"]
    get_res = agents_client.get(f"/api/agents/{agent_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == agent_id


def test_update_agent(agents_client: TestClient):
    payload = {
        "name": "Nova",
        "model": "llama3.1",
    }
    created = agents_client.post("/api/agents", json=payload).json()
    agent_id = created["id"]

    update_payload = {"name": "Nova Pro", "uses_count": 500}
    upd_res = agents_client.put(f"/api/agents/{agent_id}", json=update_payload)
    assert upd_res.status_code == 200
    updated = upd_res.json()
    assert updated["name"] == "Nova Pro"
    assert updated["uses_count"] == 500


def test_delete_agent(agents_client: TestClient):
    created = agents_client.post("/api/agents", json={"name": "TempBot"}).json()
    agent_id = created["id"]

    del_res = agents_client.delete(f"/api/agents/{agent_id}")
    assert del_res.status_code == 204

    get_res = agents_client.get(f"/api/agents/{agent_id}")
    assert get_res.status_code == 404

