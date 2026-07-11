from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import models as models_router
from services.data import connect_db, init_db


@pytest.fixture()
def models_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    def connect_temp_db() -> sqlite3.Connection:
        return connect_db(tmp_path)

    monkeypatch.setattr(models_router, "connect_db", connect_temp_db)
    app = FastAPI()
    app.include_router(models_router.router)
    return TestClient(app)


def create_model(client: TestClient) -> dict:
    payload = {
        "name": "GPT Test",
        "provider": "OpenAI",
        "description": "Test model",
        "input_cost_per_1m": 1.25,
        "output_cost_per_1m": 4.5,
        "max_context_length": 8192,
        "config": {"tier": "eval"},
    }
    response = client.post("/api/models", json=payload)
    assert response.status_code == 201
    return response.json()


def test_init_db_creates_model_registry_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    init_db(conn)

    table_rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name IN ('models', 'model_usage')"
    ).fetchall()
    index_rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'index' AND name LIKE 'idx_model_usage_%'"
    ).fetchall()

    conn.close()

    assert {row["name"] for row in table_rows} == {"models", "model_usage"}
    assert {row["name"] for row in index_rows} == {
        "idx_model_usage_model_id",
        "idx_model_usage_timestamp",
    }


def test_model_crud_when_model_exists(models_client: TestClient) -> None:
    created = create_model(models_client)
    model_id = created["id"]

    list_response = models_client.get("/api/models")
    get_response = models_client.get(f"/api/models/{model_id}")
    update_response = models_client.put(
        f"/api/models/{model_id}",
        json={"name": "GPT Updated", "config": {"tier": "prod"}},
    )
    delete_response = models_client.delete(f"/api/models/{model_id}")
    missing_response = models_client.get(f"/api/models/{model_id}")

    assert list_response.status_code == 200
    assert [model["id"] for model in list_response.json()] == [model_id]
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "GPT Test"
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "GPT Updated"
    assert update_response.json()["config"] == {"tier": "prod"}
    assert delete_response.status_code == 200
    assert delete_response.json() == {"status": "deleted", "id": model_id}
    assert missing_response.status_code == 404


def test_model_usage_stats_when_usage_exists(
    models_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def connect_temp_db() -> sqlite3.Connection:
        return connect_db(tmp_path)

    monkeypatch.setattr(models_router, "connect_db", connect_temp_db)
    created = create_model(models_client)
    model_id = created["id"]

    conn = connect_db(tmp_path)
    conn.execute(
        """
        INSERT INTO model_usage (id, model_id, session_id, input_tokens, output_tokens, cost, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (str(uuid4()), model_id, "session-1", 100, 50, 0.25, "2026-07-09T01:00:00"),
    )
    conn.execute(
        """
        INSERT INTO model_usage (id, model_id, session_id, input_tokens, output_tokens, cost, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (str(uuid4()), model_id, "session-2", 200, 75, 0.5, "2026-07-09T02:00:00"),
    )
    conn.commit()
    conn.close()

    usage_response = models_client.get(f"/api/models/{model_id}/usage")
    summary_response = models_client.get("/api/models/usage/summary")

    assert usage_response.status_code == 200
    assert usage_response.json() == {
        "model_id": model_id,
        "model_name": "GPT Test",
        "total_input_tokens": 300,
        "total_output_tokens": 125,
        "total_cost": 0.75,
        "request_count": 2,
        "last_used": "2026-07-09T02:00:00",
    }
    assert summary_response.status_code == 200
    assert summary_response.json()["total_input_tokens"] == 300
    assert summary_response.json()["total_output_tokens"] == 125
    assert summary_response.json()["total_cost"] == 0.75
    assert summary_response.json()["request_count"] == 2


def test_models_config_uses_environment(
    models_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENT_MODEL", "custom-model")
    monkeypatch.setenv("AGENT_OPENAI_BASE_URL", "https://example.test/v1")

    config_response = models_client.get("/api/models/config")
    current_response = models_client.get("/api/models/current")

    assert config_response.status_code == 200
    assert config_response.json() == {
        "default_model": "custom-model",
        "base_url": "https://example.test/v1",
    }
    assert current_response.status_code == 200
    assert current_response.json() == {
        "id": "custom-model",
        "name": "custom-model",
        "provider": "Default",
    }


def test_model_endpoints_return_404_when_missing(models_client: TestClient) -> None:
    model_id = str(uuid4())

    get_response = models_client.get(f"/api/models/{model_id}")
    update_response = models_client.put(f"/api/models/{model_id}", json={"name": "Missing"})
    delete_response = models_client.delete(f"/api/models/{model_id}")
    usage_response = models_client.get(f"/api/models/{model_id}/usage")

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    assert usage_response.status_code == 404
