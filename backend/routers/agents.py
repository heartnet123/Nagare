"""Agent routes — CRUD operations with user ownership."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from models.agent import AgentCreate, AgentUpdate, AgentResponse
from middleware.auth import get_current_user_from_cookie
from services.data import connect_db
from services.agent.skills import SkillsStore

router = APIRouter(prefix="/api/agents", tags=["agents"])

_SKILLS_DIR = Path(__file__).resolve().parents[1] / "data" / "skills"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_loads(val, default):
    if not val:
        return default
    try:
        return json.loads(val)
    except Exception:
        return default


def _row_to_agent(row) -> dict:
    """Convert database row to agent dict."""
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "model": row["model"],
        "system_prompt": row["system_prompt"] or "",
        "skills": _json_loads(row["skills"], []),
        "type": row["type"] or "chat",
        "status": row["status"] or "active",
        "role_title": row["role_title"] if "role_title" in row.keys() and row["role_title"] else "",
        "category": row["category"] if "category" in row.keys() and row["category"] else "Custom",
        "description": row["description"] if "description" in row.keys() and row["description"] else "",
        "tags": _json_loads(row["tags"] if "tags" in row.keys() else None, []),
        "capabilities": _json_loads(row["capabilities"] if "capabilities" in row.keys() else None, []),
        "tools": _json_loads(row["tools"] if "tools" in row.keys() else None, []),
        "recent_wins": _json_loads(row["recent_wins"] if "recent_wins" in row.keys() else None, []),
        "uses_count": row["uses_count"] if "uses_count" in row.keys() and row["uses_count"] is not None else 0,
        "completion_rate": row["completion_rate"] if "completion_rate" in row.keys() and row["completion_rate"] is not None else 95,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_agent_or_404(agent_id: str, user_id: str) -> dict:
    conn = connect_db()
    try:
        row = conn.execute(
            "SELECT * FROM agents WHERE id = ? AND user_id = ?",
            (agent_id, user_id),
        ).fetchone()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found",
            )
        return _row_to_agent(row)
    finally:
        conn.close()


@router.get("", response_model=List[AgentResponse])
async def list_agents(current_user: dict = Depends(get_current_user_from_cookie)):
    """List all agents owned by current user."""
    conn = connect_db()
    try:
        rows = conn.execute(
            "SELECT * FROM agents WHERE user_id = ? ORDER BY created_at DESC",
            (current_user["id"],),
        ).fetchall()
        return [_row_to_agent(row) for row in rows]
    finally:
        conn.close()


@router.get("/skills")
async def list_skills():
    """List available skills."""
    store = SkillsStore(_SKILLS_DIR)
    return store.list()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, current_user: dict = Depends(get_current_user_from_cookie)):
    """Get specific agent owned by user."""
    return _get_agent_or_404(agent_id, current_user["id"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentCreate, current_user: dict = Depends(get_current_user_from_cookie)):
    """Create agent."""
    now = _utcnow_iso()
    agent_id = str(uuid.uuid4())

    conn = connect_db()
    try:
        conn.execute(
            """
            INSERT INTO agents (
                id, user_id, name, model, system_prompt, skills, type, status,
                role_title, category, description, tags, capabilities, tools, recent_wins,
                uses_count, completion_rate, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                current_user["id"],
                agent.name,
                agent.model,
                agent.system_prompt,
                json.dumps(agent.skills),
                agent.type,
                agent.status,
                agent.role_title,
                agent.category,
                agent.description,
                json.dumps(agent.tags),
                json.dumps(agent.capabilities),
                json.dumps(agent.tools),
                json.dumps(agent.recent_wins),
                agent.uses_count,
                agent.completion_rate,
                now,
                now,
            ),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent: {e}",
        )
    finally:
        conn.close()

    return _get_agent_or_404(agent_id, current_user["id"])


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    updates: AgentUpdate,
    current_user: dict = Depends(get_current_user_from_cookie),
):
    """Update agent."""
    existing = _get_agent_or_404(agent_id, current_user["id"])

    now = _utcnow_iso()
    fields = []
    params = []

    mapping = [
        ("name", updates.name, False),
        ("model", updates.model, False),
        ("system_prompt", updates.system_prompt, False),
        ("skills", updates.skills, True),
        ("type", updates.type, False),
        ("status", updates.status, False),
        ("role_title", updates.role_title, False),
        ("category", updates.category, False),
        ("description", updates.description, False),
        ("tags", updates.tags, True),
        ("capabilities", updates.capabilities, True),
        ("tools", updates.tools, True),
        ("recent_wins", updates.recent_wins, True),
        ("uses_count", updates.uses_count, False),
        ("completion_rate", updates.completion_rate, False),
    ]

    for col, val, is_json in mapping:
        if val is not None:
            fields.append(f"{col} = ?")
            params.append(json.dumps(val) if is_json else val)

    if not fields:
        return existing

    fields.append("updated_at = ?")
    params.extend([now, agent_id, current_user["id"]])

    conn = connect_db()
    try:
        conn.execute(
            f"UPDATE agents SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params,
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update agent: {e}",
        )
    finally:
        conn.close()

    return _get_agent_or_404(agent_id, current_user["id"])


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user_from_cookie)):
    """Delete agent."""
    _get_agent_or_404(agent_id, current_user["id"])
    conn = connect_db()
    try:
        conn.execute(
            "DELETE FROM agents WHERE id = ? AND user_id = ?",
            (agent_id, current_user["id"]),
        )
        conn.commit()
    finally:
        conn.close()

