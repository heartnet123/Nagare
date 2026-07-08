"""Agent configuration REST endpoints — GET / PUT / DELETE /api/agent/config.

Settings are persisted to ``backend/data/agent_config.json`` and fall back to
environment variables (same defaults as ``AgentSettings.from_env()``) when the
file does not exist.

The ``api_key`` field is write-only: it is stored in the JSON file but is
**never** included in any response body.  Callers learn whether a key is set
via the boolean ``api_key_set`` field.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from models.agent_config import AgentConfigResponse, AgentConfigUpdate

router = APIRouter(prefix="/api/agent/config", tags=["agent-config"])

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# backend/routers/agent_config.py  →  backend/  →  project root
_BACKEND_DIR: Path = Path(__file__).resolve().parents[1]
_DATA_DIR: Path = _BACKEND_DIR / "data"
_CONFIG_PATH: Path = _DATA_DIR / "agent_config.json"
_PROJECT_ROOT: Path = _BACKEND_DIR.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _env_defaults() -> dict[str, Any]:
    """Return defaults derived from environment variables."""
    return {
        "base_url": os.environ.get("AGENT_OPENAI_BASE_URL", "http://localhost:11434/v1"),
        "api_key": os.environ.get("AGENT_OPENAI_API_KEY", "ollama"),
        "model": os.environ.get("AGENT_MODEL", "llama3.1"),
        "max_rounds": int(os.environ.get("AGENT_MAX_ROUNDS", "8")),
        "workspace": os.environ.get("AGENT_WORKSPACE", str(_PROJECT_ROOT)),
        "system_prompt_append": "",
    }


def _load_file_cfg() -> dict[str, Any]:
    """Load persisted config; return empty dict if missing or corrupt."""
    if not _CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(_CONFIG_PATH.read_text("utf-8"))
    except Exception:
        return {}


def _merged_cfg() -> dict[str, Any]:
    """Merge file config over env defaults (file values take precedence)."""
    cfg = _env_defaults()
    cfg.update(_load_file_cfg())
    return cfg


def _save_cfg(cfg: dict[str, Any]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def _to_response(cfg: dict[str, Any]) -> AgentConfigResponse:
    return AgentConfigResponse(
        base_url=cfg["base_url"],
        model=cfg["model"],
        max_rounds=int(cfg["max_rounds"]),
        workspace=cfg["workspace"],
        system_prompt_append=cfg.get("system_prompt_append", ""),
        api_key_set=bool(cfg.get("api_key", "")),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=AgentConfigResponse)
async def get_agent_config() -> AgentConfigResponse:
    """Return current agent configuration. api_key is never included in the response."""
    return _to_response(_merged_cfg())


@router.put("", response_model=AgentConfigResponse)
async def update_agent_config(update: AgentConfigUpdate) -> AgentConfigResponse:
    """Merge provided fields over current config and persist to data/agent_config.json."""
    cfg = _merged_cfg()

    if update.base_url is not None:
        cfg["base_url"] = update.base_url
    # api_key: only overwrite if explicitly provided and non-empty
    if update.api_key:
        cfg["api_key"] = update.api_key
    if update.model is not None:
        cfg["model"] = update.model
    if update.max_rounds is not None:
        cfg["max_rounds"] = update.max_rounds
    if update.workspace is not None:
        cfg["workspace"] = update.workspace
    if update.system_prompt_append is not None:
        cfg["system_prompt_append"] = update.system_prompt_append

    _save_cfg(cfg)
    return _to_response(cfg)


@router.delete("")
async def reset_agent_config() -> dict:
    """Delete persisted config file, reverting the agent to environment defaults."""
    if _CONFIG_PATH.exists():
        _CONFIG_PATH.unlink()
    return {"ok": True, "message": "Reset to environment defaults"}
