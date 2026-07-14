import os

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ["NAGARE_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from main import app
from services.data import connect_db


def test_connection_url_validation(monkeypatch, tmp_path):
    monkeypatch.setattr("services.data.default_data_dir", lambda: tmp_path)
    client = TestClient(app)
    response = client.post("/api/settings/rag-connections/test", json={"base_url": "file:///tmp", "model": "x", "api_key": "secret"})
    assert response.status_code in {401, 403, 422}


def test_schema_has_rag_connections(tmp_path):
    with connect_db(tmp_path) as db:
        assert db.execute("select name from sqlite_master where name = 'rag_connections'").fetchone()
