from __future__ import annotations

import ipaddress
import os
import secrets
import socket
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Depends

from middleware.auth import get_current_user_from_cookie, validate_csrf_token

from fastapi import APIRouter, HTTPException

from models.rag_connections import (
    RagConnectionCreate, RagConnectionResponse, RagConnectionTest,
    RagConnectionTestResponse,
)
from services.data import connect_db

router = APIRouter(prefix="/api/settings/rag-connections", tags=["rag-connections"])
_TIMEOUT = 8


def _cipher() -> Fernet:
    value = os.environ.get("NAGARE_ENCRYPTION_KEY")
    if not value:
        raise RuntimeError("NAGARE_ENCRYPTION_KEY is not configured")
    return Fernet(value.encode())


def _crypt(value: str) -> str:
    return _cipher().encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    try:
        return _cipher().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise HTTPException(status_code=503, detail="Stored credential unavailable") from exc


def _validate_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise HTTPException(status_code=422, detail="Invalid endpoint URL")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)}
        if any(not ipaddress.ip_address(address).is_global for address in addresses):
            raise HTTPException(status_code=422, detail="Endpoint address is not allowed")
    except socket.gaierror as exc:
        raise HTTPException(status_code=422, detail="Endpoint host cannot be resolved") from exc
    return value.rstrip("/")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public(row: sqlite3.Row) -> RagConnectionResponse:
    return RagConnectionResponse(id=row["id"], name=row["name"], base_url=row["base_url"], model=row["model"], api_key_set=True, created_at=row["created_at"], updated_at=row["updated_at"])

@router.get("", response_model=list[RagConnectionResponse])
def list_connections(user: dict = Depends(get_current_user_from_cookie)):
    with connect_db() as db:
        return [_public(row) for row in db.execute("select * from rag_connections order by created_at desc")]

@router.post("", response_model=RagConnectionResponse, status_code=201, dependencies=[Depends(validate_csrf_token)])
def create_connection(data: RagConnectionCreate, user: dict = Depends(get_current_user_from_cookie)):
    base_url = _validate_url(str(data.base_url))
    now = _now()
    row = (secrets.token_urlsafe(12), data.name.strip(), base_url, data.model.strip(), _crypt(data.api_key), now, now)
    with connect_db() as db:
        db.execute("insert into rag_connections values (?, ?, ?, ?, ?, ?, ?)", row)
        db.commit()
        return _public(db.execute("select * from rag_connections where id = ?", (row[0],)).fetchone())

@router.post("/test", response_model=RagConnectionTestResponse, dependencies=[Depends(validate_csrf_token)])
def test_connection(data: RagConnectionTest, user: dict = Depends(get_current_user_from_cookie)):
    base_url = _validate_url(str(data.base_url))
    request = urllib.request.Request(f"{base_url}/models", headers={"Authorization": f"Bearer {data.api_key}"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            if 200 <= response.status < 300:
                return {"ok": True, "message": "Connection successful"}
            return {"ok": False, "message": "Endpoint rejected request"}
    except (urllib.error.URLError, TimeoutError, OSError):
        return {"ok": False, "message": "Connection failed or timed out"}
