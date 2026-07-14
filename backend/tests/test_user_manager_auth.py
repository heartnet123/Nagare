from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from middleware.auth import verify_password
from services.data import init_db
import services.user_manager as user_manager_module
from services.user_manager import UserManager


@pytest.fixture()
def temp_connect_db(monkeypatch: pytest.MonkeyPatch) -> Path:
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "app.db"

        def connect_temp_db() -> sqlite3.Connection:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            init_db(conn)
            return conn

        monkeypatch.setattr(user_manager_module, "connect_db", connect_temp_db)
        yield db_path


def test_create_user_hashes_password_and_persists_user(temp_connect_db: Path) -> None:
    manager = UserManager()

    created = manager.create_user("alice", "password123")

    assert created["username"] == "alice"

    stored = manager.get_user_by_username("alice")
    assert stored is not None
    assert stored["username"] == "alice"
    assert verify_password("password123", stored["password_hash"]) is True
