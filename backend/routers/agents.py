from fastapi import APIRouter, HTTPException
from typing import List
from models.agent import AgentResponse, AgentCreate

router = APIRouter(prefix="/api/agents", tags=["agents"])

MOCK_AGENTS = [
    {"id": "agent-1", "name": "Legal RAG", "type": "rag", "status": "active", "requests": 12847, "latency": 342.0},
    {"id": "agent-2", "name": "Support Bot", "type": "chat", "status": "active", "requests": 9203, "latency": 189.0},
    {"id": "agent-3", "name": "Search Assistant", "type": "search", "status": "inactive", "requests": 5021, "latency": 156.0}
]


@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all agents"""
    return MOCK_AGENTS


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get specific agent"""
    agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(agent: AgentCreate):
    """Create new agent"""
    new_agent = {
        "id": f"agent-{len(MOCK_AGENTS) + 1}",
        **agent.dict(),
        "requests": 0,
        "latency": 0.0
    }
    MOCK_AGENTS.append(new_agent)
    return new_agent
