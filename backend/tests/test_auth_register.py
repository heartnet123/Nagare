from __future__ import annotations

from fastapi import Response
import pytest

from models.user import UserCreate
from routers import auth
from services import user_manager as user_manager_module
from services.data import connect_db
from services.user_manager import UserManager


class _FakeUserManager:
    def user_exists(self, username: str) -> bool:
        return False

    def create_user(self, username: str, password: str) -> dict[str, str]:
        return {"id": "user-123", "username": username, "created_at": "2026-07-09T00:00:00Z"}


@pytest.mark.anyio
async def test_register_returns_token_and_sets_cookies(monkeypatch) -> None:
    monkeypatch.setattr(auth, "user_manager", _FakeUserManager())
    captured: dict[str, str] = {}

    def capture_cookies(response: Response, access_token: str) -> None:
        captured["access_token"] = access_token

    monkeypatch.setattr(auth, "set_auth_cookies", capture_cookies)
    response = Response()

    token = await auth.register(UserCreate(username="alice", password="password123"), response)

    assert token.access_token == captured["access_token"]


@pytest.mark.anyio
async def test_register_accepts_normal_password_with_installed_bcrypt(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(user_manager_module, "connect_db", lambda: connect_db(tmp_path))
    monkeypatch.setattr(auth, "user_manager", UserManager())

    token = await auth.register(
        UserCreate(username="bcrypt-user", password="password123"),
        Response(),
    )

    assert token.access_token
