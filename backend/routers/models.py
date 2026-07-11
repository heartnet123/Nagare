from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from services.data import connect_db

router = APIRouter(prefix="/api/models", tags=["models"])


class ModelCreate(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    description: str | None = None
    input_cost_per_1m: float = 0.0
    output_cost_per_1m: float = 0.0
    max_context_length: int = 4096
    config: dict[str, Any] = Field(default_factory=dict)


class ModelUpdate(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str | None = Field(default=None, min_length=1)
    provider: str | None = Field(default=None, min_length=1)
    description: str | None = None
    input_cost_per_1m: float | None = None
    output_cost_per_1m: float | None = None
    max_context_length: int | None = None
    config: dict[str, Any] | None = None


class ModelResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    provider: str
    description: str | None = None
    input_cost_per_1m: float = 0.0
    output_cost_per_1m: float = 0.0
    max_context_length: int = 4096
    is_active: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class UsageStats(BaseModel):
    model_config = ConfigDict(frozen=True)

    model_id: str
    model_name: str
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    request_count: int
    last_used: str | None = None


class ModelUsageSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    models: list[UsageStats]
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float
    request_count: int


class CurrentModelConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    default_model: str
    base_url: str


class CurrentModel(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    provider: str


def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat()


def _parse_config(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def _model_response(row) -> ModelResponse:
    return ModelResponse(
        id=row["id"],
        name=row["name"],
        provider=row["provider"],
        description=row["description"],
        input_cost_per_1m=row["input_cost_per_1m"] or 0.0,
        output_cost_per_1m=row["output_cost_per_1m"] or 0.0,
        max_context_length=row["max_context_length"] or 4096,
        is_active=bool(row["is_active"]),
        config=_parse_config(row["config"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _usage_stats(row) -> UsageStats:
    return UsageStats(
        model_id=row["model_id"],
        model_name=row["model_name"],
        total_input_tokens=row["total_input_tokens"] or 0,
        total_output_tokens=row["total_output_tokens"] or 0,
        total_cost=row["total_cost"] or 0.0,
        request_count=row["request_count"] or 0,
        last_used=row["last_used"],
    )


def _get_model_row(model_id: str):
    conn = connect_db()
    try:
        return conn.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
    finally:
        conn.close()


@router.get("/config", response_model=CurrentModelConfig)
async def get_models_config() -> CurrentModelConfig:
    return CurrentModelConfig(
        default_model=os.getenv("AGENT_MODEL", "llama3.1"),
        base_url=os.getenv("AGENT_OPENAI_BASE_URL", "http://localhost:11434/v1"),
    )


@router.get("/current", response_model=CurrentModel)
async def get_current_model() -> CurrentModel:
    default_model = os.getenv("AGENT_MODEL", "llama3.1")
    return CurrentModel(id=default_model, name=default_model, provider="Default")


@router.get("/usage/summary", response_model=ModelUsageSummary)
async def get_usage_summary() -> ModelUsageSummary:
    conn = connect_db()
    try:
        rows = conn.execute(
            """
            SELECT m.id AS model_id, m.name AS model_name,
                   COALESCE(SUM(u.input_tokens), 0) AS total_input_tokens,
                   COALESCE(SUM(u.output_tokens), 0) AS total_output_tokens,
                   COALESCE(SUM(u.cost), 0.0) AS total_cost,
                   COUNT(u.id) AS request_count,
                   MAX(u.timestamp) AS last_used
            FROM models m
            LEFT JOIN model_usage u ON u.model_id = m.id
            GROUP BY m.id, m.name
            ORDER BY m.name ASC
            """
        ).fetchall()
    finally:
        conn.close()

    models = [_usage_stats(row) for row in rows]
    return ModelUsageSummary(
        models=models,
        total_input_tokens=sum(model.total_input_tokens for model in models),
        total_output_tokens=sum(model.total_output_tokens for model in models),
        total_cost=sum(model.total_cost for model in models),
        request_count=sum(model.request_count for model in models),
    )


@router.get("", response_model=list[ModelResponse])
async def list_models() -> list[ModelResponse]:
    conn = connect_db()
    try:
        rows = conn.execute("SELECT * FROM models ORDER BY name ASC").fetchall()
    finally:
        conn.close()
    return [_model_response(row) for row in rows]


@router.post("", response_model=ModelResponse, status_code=201)
async def create_model(model: ModelCreate) -> ModelResponse:
    model_id = str(uuid4())
    now = _utcnow_iso()
    conn = connect_db()
    try:
        conn.execute(
            """
            INSERT INTO models (
                id, name, provider, description, input_cost_per_1m,
                output_cost_per_1m, max_context_length, config, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                model_id,
                model.name,
                model.provider,
                model.description,
                model.input_cost_per_1m,
                model.output_cost_per_1m,
                model.max_context_length,
                json.dumps(model.config),
                now,
                now,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM models WHERE id = ?", (model_id,)).fetchone()
    finally:
        conn.close()
    return _model_response(row)


@router.get("/{model_id}/usage", response_model=UsageStats)
async def get_model_usage(model_id: str) -> UsageStats:
    if _get_model_row(model_id) is None:
        raise HTTPException(status_code=404, detail="Model not found")

    conn = connect_db()
    try:
        row = conn.execute(
            """
            SELECT m.id AS model_id, m.name AS model_name,
                   COALESCE(SUM(u.input_tokens), 0) AS total_input_tokens,
                   COALESCE(SUM(u.output_tokens), 0) AS total_output_tokens,
                   COALESCE(SUM(u.cost), 0.0) AS total_cost,
                   COUNT(u.id) AS request_count,
                   MAX(u.timestamp) AS last_used
            FROM models m
            LEFT JOIN model_usage u ON u.model_id = m.id
            WHERE m.id = ?
            GROUP BY m.id, m.name
            """,
            (model_id,),
        ).fetchone()
    finally:
        conn.close()
    return _usage_stats(row)


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str) -> ModelResponse:
    row = _get_model_row(model_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return _model_response(row)


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(model_id: str, model: ModelUpdate) -> ModelResponse:
    if _get_model_row(model_id) is None:
        raise HTTPException(status_code=404, detail="Model not found")

    updates = []
    params = []
    for field, value in model.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = ?")
        params.append(json.dumps(value) if field == "config" else value)

    if updates:
        updates.append("updated_at = ?")
        params.append(_utcnow_iso())
        params.append(model_id)
        conn = connect_db()
        try:
            conn.execute(f"UPDATE models SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        finally:
            conn.close()

    row = _get_model_row(model_id)
    return _model_response(row)


@router.delete("/{model_id}")
async def delete_model(model_id: str) -> dict[str, str]:
    if _get_model_row(model_id) is None:
        raise HTTPException(status_code=404, detail="Model not found")

    conn = connect_db()
    try:
        conn.execute("DELETE FROM models WHERE id = ?", (model_id,))
        conn.commit()
    finally:
        conn.close()
    return {"status": "deleted", "id": model_id}
