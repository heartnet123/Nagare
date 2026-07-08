from pydantic import BaseModel
from typing import List, Optional


class AgentBase(BaseModel):
    name: str
    type: str = "chat"  # "rag" | "chat" | "search"
    status: str = "active"  # "active" | "inactive"
    model: str = "llama3.1"
    system_prompt: str = ""
    skills: List[str] = []


class AgentCreate(AgentBase):
    pass


class AgentResponse(AgentBase):
    id: str
    requests: int
    latency: float

    class Config:
        from_attributes = True
