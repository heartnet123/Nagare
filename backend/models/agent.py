from pydantic import BaseModel, Field
from typing import List, Optional


class AgentBase(BaseModel):
    name: str
    model: str = "llama3.1"
    system_prompt: str = ""
    skills: List[str] = []
    type: str = "chat"  # "rag" | "chat" | "search"
    status: str = "active"  # "active" | "inactive"


class AgentCreate(AgentBase):
    """Request body for creating an agent. user_id is injected from auth."""
    pass


class AgentUpdate(BaseModel):
    """Request body for updating an agent. All fields optional."""
    name: Optional[str] = None
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    skills: Optional[List[str]] = None
    type: Optional[str] = None
    status: Optional[str] = None


class AgentResponse(AgentBase):
    """Agent as returned by the API."""
    id: str
    user_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
