from pydantic import BaseModel, Field
from typing import Optional


class AgentConfigResponse(BaseModel):
    base_url: str
    model: str
    max_rounds: int
    workspace: str
    system_prompt_append: str
    api_key_set: bool  # True if a key is configured; the key itself is NEVER returned


class AgentConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None   # write-only, only used on PUT
    model: Optional[str] = None
    max_rounds: Optional[int] = Field(default=None, ge=1, le=20)
    workspace: Optional[str] = None
    system_prompt_append: Optional[str] = None
