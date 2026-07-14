"""User manager service — handles user CRUD and authentication."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from services.data import connect_db
from middleware.auth import hash_password, verify_password


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class UserManager:
    """Manages user operations in the database."""

    def create_user(self, username: str, password: str) -> dict:
        user_id = str(uuid.uuid4())
        now = _utcnow_iso()
        password_hash = hash_password(password)

        conn = connect_db()
        try:
            conn.execute(
                "INSERT INTO users (id, username, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, None, password_hash, now),
            )
            conn.commit()
            return {
                "id": user_id,
                "username": username,
                "created_at": now,
            }
        except Exception as e:
            conn.rollback()
            raise ValueError(f"Failed to create user: {e}") from e
        finally:
            conn.close()

    def get_user(self, user_id: str) -> Optional[dict]:
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT id, username, created_at FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "created_at": row["created_at"],
            }
        finally:
            conn.close()

    def get_user_by_username(self, username: str) -> Optional[dict]:
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT id, username, password_hash, created_at FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if row is None:
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "password_hash": row["password_hash"],
                "created_at": row["created_at"],
            }
        finally:
            conn.close()

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user. Returns user dict if valid, None otherwise."""
        user = self.get_user_by_username(username)
        if user is None:
            return None
        if not verify_password(password, user["password_hash"]):
            return None
        return {
            "id": user["id"],
            "username": user["username"],
            "created_at": user["created_at"],
        }

    def user_exists(self, username: str = None) -> bool:
        conn = connect_db()
        try:
            if username:
                row = conn.execute(
                    "SELECT 1 FROM users WHERE username = ?", (username,)
                ).fetchone()
                if row:
                    return True
            return False
        finally:
            conn.close()
