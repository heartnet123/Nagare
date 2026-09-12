from pydantic import BaseModel, Field
from typing import List, Optional


class AgentBase(BaseModel):
    name: str
    model: str = "llama3.1"
    system_prompt: str = ""
    skills: List[str] = []
    type: str = "chat"  # "rag" | "chat" | "search"
    status: str = "active"  # "active" | "inactive"
    role_title: str = ""
    category: str = "Custom"
    description: str = ""
    tags: List[str] = []
    capabilities: List[str] = []
    tools: List[str] = []
    recent_wins: List[dict] = []
    uses_count: int = 0
    completion_rate: int = 95


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
    role_title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    recent_wins: Optional[List[dict]] = None
    uses_count: Optional[int] = None
    completion_rate: Optional[int] = None


class AgentResponse(AgentBase):
    """Agent as returned by the API."""
    id: str
    user_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
