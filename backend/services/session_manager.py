"""
Session management — all session business logic and DB operations.

Port from Odysseus core/session_manager.py, adapted to Nagare's
plain-sqlite3 pattern (no SQLAlchemy).

Single place that handles:
- Loading/saving sessions to database
- Adding messages to sessions
- Session lifecycle (create, archive, delete)
"""

from __future__ import annotations

import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.data import connect_db

logger = logging.getLogger(__name__)


def _utcnow_iso() -> str:
    """ISO-formatted UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


def _message_timestamp_iso(dt_str: Optional[str]) -> Optional[str]:
    """Normalize a timestamp string to stable ISO format."""
    if not dt_str:
        return None
    return dt_str


def _parse_msg_content(raw: str) -> str:
    """Parse message content — deserialize JSON arrays back to strings."""
    if isinstance(raw, str) and raw.startswith("[{"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return raw  # store as-is; frontend handles multimodal
        except (json.JSONDecodeError, ValueError):
            pass
    return raw


def _now_utc_dt():
    """Naive UTC datetime for DB storage."""
    return datetime.now(timezone.utc)


class SessionManager:
    """
    Manages chat sessions with database persistence.

    Usage:
        manager = SessionManager()
        session = manager.create_session(session_id, name, model, endpoint_url)
        manager.add_message(session_id, "user", "Hello")
        session = manager.get_session(session_id)
    """

    def __init__(self):
        self.sessions: Dict[str, dict] = {}  # in-memory cache: id -> session dict
        self._load_sessions()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_sessions(self):
        """Load session metadata from the database (messages loaded on demand)."""
        conn = connect_db()
        try:
            rows = conn.execute(
                """
                SELECT id, name, model, endpoint_url, rag, archived,
                       is_important, folder, message_count,
                       total_input_tokens, total_output_tokens,
                       created_at, updated_at, last_accessed, last_message_at,
                       mode
                FROM sessions
                WHERE archived = 0 AND message_count > 0
                ORDER BY last_accessed DESC
                LIMIT 100
                """
            ).fetchall()

            loaded = 0
            for row in rows:
                try:
                    session = self._row_to_session_meta(row)
                    if session:
                        self.sessions[row["id"]] = session
                        loaded += 1
                except Exception as e:
                    logger.error(f"Error loading session {row['id']}: {e}")
                    continue

            logger.info(f"Loaded {loaded} session(s) (metadata only)")
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
        finally:
            conn.close()

    def _row_to_session_meta(self, row) -> Optional[dict]:
        """Build a session dict with empty messages list."""
        return {
            "id": row["id"],
            "name": row["name"],
            "model": row["model"] or "",
            "endpoint_url": row["endpoint_url"] or "",
            "rag": bool(row["rag"]),
            "archived": bool(row["archived"]),
            "is_important": bool(row["is_important"]),
            "folder": row["folder"],
            "message_count": row["message_count"] or 0,
            "total_input_tokens": row["total_input_tokens"] or 0,
            "total_output_tokens": row["total_output_tokens"] or 0,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_accessed": row["last_accessed"],
            "last_message_at": row["last_message_at"],
            "messages": [],
            "mode": row["mode"] if ("mode" in row.keys() and row["mode"] is not None) else "chat",
        }

    def _row_to_session(self, row, messages: List[dict]) -> dict:
        """Build a full session dict with messages from a DB row."""
        headers = {}
        return {
            "id": row["id"],
            "name": row["name"],
            "model": row["model"] or "",
            "endpoint_url": row["endpoint_url"] or "",
            "rag": bool(row["rag"]),
            "archived": bool(row["archived"]),
            "is_important": bool(row["is_important"]),
            "folder": row["folder"],
            "message_count": row["message_count"] or len(messages),
            "total_input_tokens": row["total_input_tokens"] or 0,
            "total_output_tokens": row["total_output_tokens"] or 0,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_accessed": row["last_accessed"],
            "last_message_at": row["last_message_at"],
            "messages": messages,
            "mode": row["mode"] if ("mode" in row.keys() and row["mode"] is not None) else "chat",
        }

    # ------------------------------------------------------------------
    # Session CRUD
    # ------------------------------------------------------------------

    def get_session(self, session_id: str) -> dict:
        """Get a session by ID, loading full messages from DB if needed."""
        if session_id not in self.sessions:
            return self._load_session_from_db(session_id)

        cached = self.sessions[session_id]
        # Lazy hydrate: metadata-only entries get messages on first full read
        if not cached.get("messages") and cached.get("message_count", 0) > 0:
            return self._load_session_from_db(session_id)

        # Touch last_accessed in background
        self._touch_session(session_id)
        return self.sessions[session_id]

    def _load_session_from_db(self, session_id: str) -> dict:
        """Load a full session (with messages) from the database."""
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()

            if row is None:
                raise KeyError(f"Session {session_id} not found")

            # Load messages
            msg_rows = conn.execute(
                "SELECT id, role, content, metadata, timestamp "
                "FROM chat_messages WHERE session_id = ? "
                "ORDER BY timestamp ASC",
                (session_id,),
            ).fetchall()

            messages = []
            for m in msg_rows:
                meta = None
                if m["metadata"]:
                    try:
                        meta = json.loads(m["metadata"])
                    except json.JSONDecodeError:
                        meta = {}
                messages.append({
                    "id": m["id"],
                    "role": m["role"],
                    "content": _parse_msg_content(m["content"]),
                    "metadata": meta or {},
                    "timestamp": m["timestamp"],
                })

            session = self._row_to_session(row, messages)
            self.sessions[session_id] = session
            return session

        except KeyError:
            raise
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            raise KeyError(f"Session {session_id} not found") from e
        finally:
            conn.close()

    def _touch_session(self, session_id: str):
        """Update last_accessed timestamp."""
        conn = connect_db()
        try:
            conn.execute(
                "UPDATE sessions SET last_accessed = ? WHERE id = ?",
                (_utcnow_iso(), session_id),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error updating last_accessed: {e}")
        finally:
            conn.close()

    def create_session(
        self,
        session_id: str,
        name: str,
        model: str = "",
        endpoint_url: str = "",
        mode: str = "chat",
    ) -> dict:
        """Create a new session and save to database."""
        now = _utcnow_iso()
        conn = connect_db()
        try:
            conn.execute(
                """
                INSERT INTO sessions (id, name, model, endpoint_url, rag, archived,
                    is_important, folder, message_count, total_input_tokens,
                    total_output_tokens, created_at, updated_at, last_accessed, last_message_at, mode)
                VALUES (?, ?, ?, ?, 0, 0, 0, NULL, 0, 0, 0, ?, ?, ?, NULL, ?)
                """,
                (session_id, name, model, endpoint_url, now, now, now, mode),
            )
            conn.commit()

            session = {
                "id": session_id,
                "name": name,
                "model": model,
                "endpoint_url": endpoint_url,
                "rag": False,
                "archived": False,
                "is_important": False,
                "folder": None,
                "message_count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "created_at": now,
                "updated_at": now,
                "last_accessed": now,
                "last_message_at": None,
                "messages": [],
                "mode": mode,
            }

            self.sessions[session_id] = session
            logger.info(f"Created session {session_id}")
            return session

        except Exception as e:
            conn.rollback()
            logger.error(f"Error creating session: {e}")
            raise
        finally:
            conn.close()

    def delete_session(self, session_id: str) -> bool:
        """Permanently delete a session and all its messages."""
        conn = connect_db()
        try:
            # Delete messages first (CASCADE should handle this, but be explicit)
            conn.execute(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,),
            )
            # Delete session
            conn.execute(
                "DELETE FROM sessions WHERE id = ?",
                (session_id,),
            )
            conn.commit()

            # Drop from in-memory cache
            self.sessions.pop(session_id, None)

            logger.info(f"Deleted session {session_id}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting session: {e}")
            return False
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Session updates
    # ------------------------------------------------------------------

    def update_session_name(self, session_id: str, name: str):
        """Update session name."""
        now = _utcnow_iso()
        conn = connect_db()
        try:
            conn.execute(
                "UPDATE sessions SET name = ?, updated_at = ? WHERE id = ?",
                (name, now, session_id),
            )
            conn.commit()
            if session_id in self.sessions:
                self.sessions[session_id]["name"] = name
                self.sessions[session_id]["updated_at"] = now
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating session name: {e}")
            raise
        finally:
            conn.close()

    def update_session(
        self,
        session_id: str,
        name: Optional[str] = None,
        folder: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[dict]:
        """Update session fields. Returns updated session or None if not found."""
        now = _utcnow_iso()
        conn = connect_db()
        try:
            row = conn.execute(
                "SELECT id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                return None

            updates = []
            params = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if folder is not None:
                updates.append("folder = ?")
                params.append(folder)
            if model is not None:
                updates.append("model = ?")
                params.append(model)

            if not updates:
                return self.get_session(session_id)

            updates.append("updated_at = ?")
            params.append(now)
            params.append(session_id)

            conn.execute(
                f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()

            # Update cache
            if session_id in self.sessions:
                cached = self.sessions[session_id]
                if name is not None:
                    cached["name"] = name
                if folder is not None:
                    cached["folder"] = folder
                if model is not None:
                    cached["model"] = model
                cached["updated_at"] = now

            return self.get_session(session_id)

        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating session: {e}")
            raise
        finally:
            conn.close()

    def archive_session(self, session_id: str, archived: bool = True):
        """Archive or unarchive a session."""
        now = _utcnow_iso()
        conn = connect_db()
        try:
            val = 1 if archived else 0
            conn.execute(
                "UPDATE sessions SET archived = ?, updated_at = ? WHERE id = ?",
                (val, now, session_id),
            )
            conn.commit()
            if session_id in self.sessions:
                self.sessions[session_id]["archived"] = archived
                self.sessions[session_id]["updated_at"] = now
        except Exception as e:
            conn.rollback()
            logger.error(f"Error archiving session: {e}")
            raise
        finally:
            conn.close()

    def mark_important(self, session_id: str, important: bool = True):
        """Mark a session as important (protected from cleanup)."""
        now = _utcnow_iso()
        conn = connect_db()
        try:
            val = 1 if important else 0
            conn.execute(
                "UPDATE sessions SET is_important = ?, updated_at = ? WHERE id = ?",
                (val, now, session_id),
            )
            conn.commit()
            if session_id in self.sessions:
                self.sessions[session_id]["is_important"] = important
        except Exception as e:
            conn.rollback()
            logger.error(f"Error marking session important: {e}")
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Message operations
    # ------------------------------------------------------------------

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Add a message to a session and persist to database.

        Returns the message dict with assigned id.
        """
        session = self.get_session(session_id)

        msg_id = str(uuid.uuid4())
        msg_time = _utcnow_iso()
        meta_json = json.dumps(metadata) if metadata else None

        conn = connect_db()
        try:
            # Persist message
            conn.execute(
                """
                INSERT INTO chat_messages (id, session_id, role, content, metadata, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, session_id, role, content, meta_json, msg_time),
            )

            # Update session metadata
            conn.execute(
                """
                UPDATE sessions SET
                    message_count = message_count + 1,
                    last_accessed = ?,
                    last_message_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (msg_time, msg_time, msg_time, session_id),
            )

            conn.commit()

            message = {
                "id": msg_id,
                "role": role,
                "content": content,
                "metadata": metadata or {},
                "timestamp": msg_time,
            }

            # Update in-memory cache
            session["messages"].append(message)
            session["message_count"] = len(session["messages"])
            session["last_accessed"] = msg_time
            session["last_message_at"] = msg_time
            session["updated_at"] = msg_time

            return message

        except Exception as e:
            conn.rollback()
            logger.error(f"Error persisting message: {e}")
            raise
        finally:
            conn.close()

    def get_messages(self, session_id: str) -> List[dict]:
        """Get all messages for a session."""
        session = self.get_session(session_id)
        return session.get("messages", [])

    def replace_messages(self, session_id: str, messages: List[dict]) -> bool:
        """Replace a session's persisted and in-memory history atomically."""
        session = self.get_session(session_id)
        conn = connect_db()
        try:
            # Delete all existing messages
            conn.execute(
                "DELETE FROM chat_messages WHERE session_id = ?",
                (session_id,),
            )

            # Insert new messages
            now = _utcnow_iso()
            for i, msg in enumerate(messages):
                msg_id = msg.get("id") or str(uuid.uuid4())
                meta_json = json.dumps(msg.get("metadata")) if msg.get("metadata") else None
                # Stagger timestamps to preserve order
                ts = msg.get("timestamp") or _utcnow_iso()
                conn.execute(
                    """
                    INSERT INTO chat_messages (id, session_id, role, content, metadata, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (msg_id, session_id, msg["role"], msg["content"], meta_json, ts),
                )

            # Update session count
            conn.execute(
                """
                UPDATE sessions SET
                    message_count = ?,
                    last_accessed = ?,
                    last_message_at = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (len(messages), now, now, now, session_id),
            )

            conn.commit()

            # Update in-memory
            session["messages"] = list(messages)
            session["message_count"] = len(messages)
            session["last_accessed"] = now
            session["last_message_at"] = now
            session["updated_at"] = now

            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Error replacing messages: {e}")
            return False
        finally:
            conn.close()

    def truncate_messages(self, session_id: str, keep_count: int) -> bool:
        """Truncate session history, keeping only the first keep_count messages."""
        if keep_count < 0:
            return False

        conn = connect_db()
        try:
            # Get all message IDs ordered
            rows = conn.execute(
                "SELECT id FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC",
                (session_id,),
            ).fetchall()

            if keep_count >= len(rows):
                return True  # nothing to truncate

            # Delete excess
            ids_to_delete = [r["id"] for r in rows[keep_count:]]
            placeholders = ",".join("?" for _ in ids_to_delete)
            conn.execute(
                f"DELETE FROM chat_messages WHERE id IN ({placeholders})",
                ids_to_delete,
            )

            # Update count
            conn.execute(
                "UPDATE sessions SET message_count = ? WHERE id = ?",
                (keep_count, session_id),
            )
            conn.commit()

            # Update in-memory
            if session_id in self.sessions:
                self.sessions[session_id]["messages"] = (
                    self.sessions[session_id]["messages"][:keep_count]
                )
                self.sessions[session_id]["message_count"] = keep_count

            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Error truncating session: {e}")
            return False
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_sessions(
        self,
        archived: bool = False,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> Tuple[List[dict], int]:
        """List sessions with pagination and optional search.

        Returns (sessions_list, total_count).
        """
        conn = connect_db()
        try:
            where_clauses = ["archived = ?"]
            params: list = [1 if archived else 0]

            if search:
                where_clauses.append("name LIKE ?")
                params.append(f"%{search}%")

            where = " AND ".join(where_clauses)

            # Get total count
            total = conn.execute(
                f"SELECT COUNT(*) as cnt FROM sessions WHERE {where}",
                params,
            ).fetchone()["cnt"]

            # Get page
            rows = conn.execute(
                f"""
                SELECT id, name, model, endpoint_url, rag, archived,
                       is_important, folder, message_count,
                       total_input_tokens, total_output_tokens,
                       created_at, updated_at, last_accessed, last_message_at,
                       mode
                FROM sessions
                WHERE {where}
                ORDER BY COALESCE(last_message_at, updated_at, created_at) DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            ).fetchall()

            sessions_list = []
            for row in rows:
                s = self._row_to_session_meta(row)
                if s:
                    sessions_list.append(s)

            return sessions_list, total

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return [], 0
        finally:
            conn.close()
