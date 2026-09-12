from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from middleware.auth import get_current_user_from_cookie
from services.data import connect_db

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


class DecisionCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1)
    subtitle: str = ""
    priority: str = "normal"  # urgent, high, medium, low, normal
    priority_label: str = "Normal"
    agent_name: str = "Assistant"
    agent_role: str = "Agent"
    agent_initials: str = "A"
    agent_color: str = "blue"
    comments_count: int = 0
    category: str = "Urgent"
    project: str = ""
    confidence_score: int = 90
    summary: str = ""
    key_rationale: list[str] = Field(default_factory=list)
    potential_risks: list[str] = Field(default_factory=list)
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    files: list[dict[str, Any]] = Field(default_factory=list)
    selected_alternative: str = "opt-a"


class DecisionUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    selected_alternative: Optional[str] = None
    status: Optional[str] = None
    note: Optional[str] = None


class DecisionActionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    action: str  # approve, request_changes, assign_back, reject
    note: Optional[str] = None
    selected_option_id: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    source_name: str
    preview_url: str | None = None


def _format_decision(row: Any) -> dict[str, Any]:
    data = dict(row)
    for json_col in ("key_rationale", "potential_risks", "alternatives", "files"):
        if json_col in data and isinstance(data[json_col], str):
            try:
                data[json_col] = json.loads(data[json_col])
            except Exception:
                data[json_col] = []
    # normalize alias fields for frontend compatibility
    data["rationale"] = data.get("key_rationale", [])
    data["risks"] = data.get("potential_risks", [])
    data["supporting_materials"] = data.get("files", [])
    return data


@router.get("/decisions")
async def list_decisions(
    filter: str = Query(default="all"),
    search: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user_from_cookie),
):
    conn = connect_db()
    try:
        user_id = user["id"]
        query = "select * from inbox_decisions where (user_id = ? or user_id is null)"
        params: list[Any] = [user_id]

        if filter == "urgent":
            query += " and status = 'pending' and priority in ('urgent', 'high')"
        elif filter == "today":
            query += " and status = 'pending' and (time_ago like '%hour%' or date(created_at) = date('now'))"
        elif filter == "this_week":
            query += " and status = 'pending'"
        elif filter == "approved":
            query += " and status = 'approved'"
        elif filter == "sent_back":
            query += " and status = 'sent_back'"
        else:
            # "all" view shows all pending decisions
            query += " and status = 'pending'"

        if search:
            query += " and (title like ? or subtitle like ? or summary like ?)"
            term = f"%{search}%"
            params.extend([term, term, term])

        query += " order by created_at desc"
        rows = conn.execute(query, params).fetchall()
        return [_format_decision(r) for r in rows]
    finally:
        conn.close()


@router.get("/items")
async def list_inbox_items_alias(
    filter: str = Query(default="all"),
    search: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user_from_cookie),
):
    return await list_decisions(filter=filter, search=search, user=user)


@router.post("/decisions", status_code=201)
async def create_decision(
    payload: DecisionCreate,
    user: dict = Depends(get_current_user_from_cookie),
):
    now = datetime.now(timezone.utc).isoformat()
    decision_id = str(uuid.uuid4())
    record = {
        "id": decision_id,
        "user_id": user["id"],
        "title": payload.title.strip(),
        "subtitle": payload.subtitle.strip(),
        "priority": payload.priority.lower(),
        "priority_label": payload.priority_label or payload.priority.capitalize(),
        "time_ago": "just now",
        "agent_name": payload.agent_name.strip(),
        "agent_role": payload.agent_role.strip(),
        "agent_initials": (payload.agent_name[:2] if payload.agent_name else "A").upper(),
        "agent_color": payload.agent_color or "blue",
        "comments_count": payload.comments_count,
        "category": payload.category,
        "project": payload.project,
        "confidence_score": payload.confidence_score,
        "summary": payload.summary,
        "key_rationale": json.dumps(payload.key_rationale),
        "potential_risks": json.dumps(payload.potential_risks),
        "alternatives": json.dumps(payload.alternatives),
        "files": json.dumps(payload.files),
        "status": "pending",
        "selected_alternative": payload.selected_alternative or "opt-a",
        "created_at": now,
        "updated_at": now,
    }

    conn = connect_db()
    try:
        conn.execute(
            """insert into inbox_decisions (
                id, user_id, title, subtitle, priority, priority_label, time_ago,
                agent_name, agent_role, agent_initials, agent_color, comments_count,
                category, project, confidence_score, summary, key_rationale,
                potential_risks, alternatives, files, status, selected_alternative,
                created_at, updated_at
            ) values (
                :id, :user_id, :title, :subtitle, :priority, :priority_label, :time_ago,
                :agent_name, :agent_role, :agent_initials, :agent_color, :comments_count,
                :category, :project, :confidence_score, :summary, :key_rationale,
                :potential_risks, :alternatives, :files, :status, :selected_alternative,
                :created_at, :updated_at
            )""",
            record,
        )
        conn.commit()
        created_row = conn.execute("select * from inbox_decisions where id = ?", (decision_id,)).fetchone()
        return _format_decision(created_row)
    finally:
        conn.close()


@router.get("/decisions/{decision_id}")
async def get_decision(
    decision_id: str,
    user: dict = Depends(get_current_user_from_cookie),
):
    conn = connect_db()
    try:
        row = conn.execute(
            "select * from inbox_decisions where id = ? and (user_id = ? or user_id is null)",
            (decision_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Decision not found")
        return _format_decision(row)
    finally:
        conn.close()


@router.get("/items/{item_id}")
async def get_item_alias(
    item_id: str,
    user: dict = Depends(get_current_user_from_cookie),
):
    return await get_decision(item_id, user)


@router.patch("/decisions/{decision_id}")
async def update_decision(
    decision_id: str,
    payload: DecisionUpdate,
    user: dict = Depends(get_current_user_from_cookie),
):
    conn = connect_db()
    try:
        row = conn.execute(
            "select * from inbox_decisions where id = ? and (user_id = ? or user_id is null)",
            (decision_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Decision not found")

        now = datetime.now(timezone.utc).isoformat()
        updates: list[str] = ["updated_at = ?"]
        params: list[Any] = [now]

        if payload.selected_alternative is not None:
            updates.append("selected_alternative = ?")
            params.append(payload.selected_alternative)
        if payload.status is not None:
            updates.append("status = ?")
            params.append(payload.status)

        params.append(decision_id)
        conn.execute(f"update inbox_decisions set {', '.join(updates)} where id = ?", params)
        conn.commit()

        updated_row = conn.execute("select * from inbox_decisions where id = ?", (decision_id,)).fetchone()
        return _format_decision(updated_row)
    finally:
        conn.close()


@router.post("/decisions/{decision_id}/approve")
async def approve_decision(
    decision_id: str,
    user: dict = Depends(get_current_user_from_cookie),
):
    conn = connect_db()
    try:
        row = conn.execute(
            "select * from inbox_decisions where id = ? and (user_id = ? or user_id is null)",
            (decision_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Decision not found")

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "update inbox_decisions set status = 'approved', updated_at = ? where id = ?",
            (now, decision_id),
        )
        conn.commit()
        return {"status": "ok", "new_status": "approved", "decision_id": decision_id}
    finally:
        conn.close()


@router.post("/decisions/{decision_id}/request-changes")
async def request_changes_decision(
    decision_id: str,
    user: dict = Depends(get_current_user_from_cookie),
):
    conn = connect_db()
    try:
        row = conn.execute(
            "select * from inbox_decisions where id = ? and (user_id = ? or user_id is null)",
            (decision_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Decision not found")

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "update inbox_decisions set status = 'sent_back', updated_at = ? where id = ?",
            (now, decision_id),
        )
        conn.commit()
        return {"status": "ok", "new_status": "sent_back", "decision_id": decision_id}
    finally:
        conn.close()


@router.post("/decisions/{decision_id}/assign-back")
async def assign_back_decision(
    decision_id: str,
    user: dict = Depends(get_current_user_from_cookie),
):
    conn = connect_db()
    try:
        row = conn.execute(
            "select * from inbox_decisions where id = ? and (user_id = ? or user_id is null)",
            (decision_id, user["id"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Decision not found")

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "update inbox_decisions set status = 'sent_back', updated_at = ? where id = ?",
            (now, decision_id),
        )
        conn.commit()
        return {"status": "ok", "new_status": "sent_back", "decision_id": decision_id}
    finally:
        conn.close()


@router.post("/items/{item_id}/action")
async def take_inbox_action_alias(
    item_id: str,
    payload: DecisionActionRequest,
    user: dict = Depends(get_current_user_from_cookie),
):
    if payload.action == "approve":
        return await approve_decision(item_id, user)
    elif payload.action in ("request_changes", "reject"):
        return await request_changes_decision(item_id, user)
    elif payload.action == "assign_back":
        return await assign_back_decision(item_id, user)
    raise HTTPException(status_code=400, detail=f"Unknown action {payload.action}")


@router.delete("/decisions/{decision_id}")
async def delete_decision(
    decision_id: str,
    user: dict = Depends(get_current_user_from_cookie),
):
    conn = connect_db()
    try:
        res = conn.execute(
            "delete from inbox_decisions where id = ? and (user_id = ? or user_id is null)",
            (decision_id, user["id"]),
        )
        conn.commit()
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail="Decision not found")
        return {"status": "ok", "deleted": True, "decision_id": decision_id}
    finally:
        conn.close()


@router.get("/stats")
async def get_inbox_stats(user: dict = Depends(get_current_user_from_cookie)):
    conn = connect_db()
    try:
        user_id = user["id"]
        rows = conn.execute(
            """select priority, status, created_at, updated_at
               from inbox_decisions
               where (user_id = ? or user_id is null)""",
            (user_id,),
        ).fetchall()

        pending = [r for r in rows if r["status"] == "pending"]
        approved = [r for r in rows if r["status"] == "approved"]
        sent_back = [r for r in rows if r["status"] == "sent_back"]
        urgent = [r for r in pending if r["priority"] in ("urgent", "high")]

        now = datetime.now(timezone.utc)
        today_items = []
        sla_risk = 0
        for r in pending:
            try:
                dt = datetime.fromisoformat(r["created_at"])
                age_hours = (now - dt).total_seconds() / 3600.0
                if age_hours <= 24:
                    today_items.append(r)
                if age_hours > 24 or r["priority"] == "urgent":
                    sla_risk += 1
            except Exception:
                pass

        # Calculate average approval time in hours from real approved items
        avg_approval_hours = 0.0
        if approved:
            durations = []
            for r in approved:
                try:
                    c_dt = datetime.fromisoformat(r["created_at"])
                    u_dt = datetime.fromisoformat(r["updated_at"])
                    durations.append(max(0.1, (u_dt - c_dt).total_seconds() / 3600.0))
                except Exception:
                    durations.append(2.8)
            avg_approval_hours = sum(durations) / len(durations) if durations else 2.8

        avg_str = f"{avg_approval_hours:.1f}h" if approved else "2.8h"

        return {
            "avg_time": avg_str,
            "avg_time_change": "-32%",
            "pending_count": len(pending),
            "sla_risk_count": sla_risk,
            "approved_count": len(approved),
            "sent_back_count": len(sent_back),
            "urgent_count": len(urgent),
            "today_count": len(today_items),
            "this_week_count": len(pending),
            "total_pending": len(pending),
        }
    finally:
        conn.close()


# Legacy projects fallback
@router.get("/projects")
async def list_projects(user: dict = Depends(get_current_user_from_cookie)):
    conn = connect_db()
    try:
        rows = conn.execute(
            "select * from inbox_projects where user_id = ? order by updated_at desc",
            (user["id"],),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


@router.post("/projects", status_code=201)
async def create_project(
    payload: ProjectCreate, user: dict = Depends(get_current_user_from_cookie)
):
    now = datetime.now(timezone.utc).isoformat()
    project = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": payload.name.strip(),
        "source_name": payload.source_name.strip(),
        "preview_url": payload.preview_url,
        "status": "queued",
        "created_at": now,
        "updated_at": now,
    }
    conn = connect_db()
    try:
        conn.execute(
            "insert into inbox_projects (id,user_id,name,source_name,preview_url,status,created_at,updated_at) values (:id,:user_id,:name,:source_name,:preview_url,:status,:created_at,:updated_at)",
            project,
        )
        conn.commit()
        return project
    finally:
        conn.close()
