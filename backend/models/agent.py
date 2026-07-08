from pydantic import BaseModel


class AgentBase(BaseModel):
    name: str
    type: str  # "rag" | "chat" | "search"
    status: str  # "active" | "inactive"


class AgentCreate(AgentBase):
    pass


class AgentResponse(AgentBase):
    id: str
    requests: int
    latency: float

    class Config:
        from_attributes = True
