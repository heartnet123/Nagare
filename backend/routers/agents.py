"""Agent routes — CRUD operations with user ownership."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from models.agent import AgentCreate, AgentUpdate, AgentResponse
from middleware.auth import get_current_user
from services.data import connect_db
from services.agent.skills import SkillsStore
from pathlib import Path

router = APIRouter(prefix="/api/agents", tags=["agents"])

_SKILLS_DIR = Path(__file__).resolve().parents[1] / "data" / "skills"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_agent(row) -> dict:
    """Convert a database row to an agent dict."""
    skills_json = row["skills"] or "[]"
    try:
        skills = json.loads(skills_json)
    except json.JSONDecodeError:
        skills = []
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "name": row["name"],
        "model": row["model"],
        "system_prompt": row["system_prompt"] or "",
        "skills": skills,
        "type": row["type"] or "chat",
        "status": row["status"] or "active",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_agent_or_404(agent_id: str, user_id: str) -> dict:
    """Get an agent by ID, enforcing user ownership. Raises 404 if not found or not owned."""
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


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@router.get("", response_model=List[AgentResponse])
async def list_agents(current_user: dict = Depends(get_current_user)):
    """List all agents owned by the current user."""
    conn = connect_db()
    try:
        rows = conn.execute(
            "SELECT * FROM agents WHERE user_id = ? ORDER BY created_at DESC",
            (current_user["id"],),
        ).fetchall()
        return [_row_to_agent(row) for row in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Skills
# ---------------------------------------------------------------------------


@router.get("/skills")
async def list_skills():
    """List available skills from the skills store."""
    store = SkillsStore(_SKILLS_DIR)
    return store.list()


# ---------------------------------------------------------------------------
# Get single agent
# ---------------------------------------------------------------------------


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific agent owned by the current user."""
    return _get_agent_or_404(agent_id, current_user["id"])


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(agent: AgentCreate, current_user: dict = Depends(get_current_user)):
    """Create a new agent for the current user."""
    now = _utcnow_iso()
    agent_id = str(uuid.uuid4())
    skills_json = json.dumps(agent.skills)

    conn = connect_db()
    try:
        conn.execute(
            """
            INSERT INTO agents (id, user_id, name, model, system_prompt, skills, type, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_id,
                current_user["id"],
                agent.name,
                agent.model,
                agent.system_prompt,
                skills_json,
                agent.type,
                agent.status,
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

    return {
        "id": agent_id,
        "user_id": current_user["id"],
        "name": agent.name,
        "model": agent.model,
        "system_prompt": agent.system_prompt,
        "skills": agent.skills,
        "type": agent.type,
        "status": agent.status,
        "created_at": now,
        "updated_at": now,
    }


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    updates: AgentUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an agent owned by the current user."""
    # Verify ownership
    existing = _get_agent_or_404(agent_id, current_user["id"])

    now = _utcnow_iso()
    update_fields = []
    params = []

    if updates.name is not None:
        update_fields.append("name = ?")
        params.append(updates.name)
    if updates.model is not None:
        update_fields.append("model = ?")
        params.append(updates.model)
    if updates.system_prompt is not None:
        update_fields.append("system_prompt = ?")
        params.append(updates.system_prompt)
    if updates.skills is not None:
        update_fields.append("skills = ?")
        params.append(json.dumps(updates.skills))
    if updates.type is not None:
        update_fields.append("type = ?")
        params.append(updates.type)
    if updates.status is not None:
        update_fields.append("status = ?")
        params.append(updates.status)

    if not update_fields:
        return existing

    update_fields.append("updated_at = ?")
    params.append(now)
    params.append(agent_id)
    params.append(current_user["id"])

    conn = connect_db()
    try:
        conn.execute(
            f"UPDATE agents SET {', '.join(update_fields)} WHERE id = ? AND user_id = ?",
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

    # Return updated agent
    return _get_agent_or_404(agent_id, current_user["id"])


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, current_user: dict = Depends(get_current_user)):
    """Permanently delete an agent owned by the current user."""
    # Verify ownership (will raise 404 if not found)
    _get_agent_or_404(agent_id, current_user["id"])

    conn = connect_db()
    try:
        conn.execute(
            "DELETE FROM agents WHERE id = ? AND user_id = ?",
            (agent_id, current_user["id"]),
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete agent: {e}",
        )
    finally:
        conn.close()
