import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException
from models.agent import AgentResponse, AgentCreate
from services.agent.skills import SkillsStore

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Persistent agent file location
_DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_AGENTS_PATH = _DATA_DIR / "agents.json"
_SKILLS_DIR = _DATA_DIR / "skills"

DEFAULT_AGENTS = [
    {
        "id": "agent-1",
        "name": "Legal RAG",
        "type": "rag",
        "status": "active",
        "requests": 12847,
        "latency": 342.0,
        "model": "llama3.1",
        "system_prompt": "You are a legal document query helper.",
        "skills": ["project"]
    },
    {
        "id": "agent-2",
        "name": "Support Bot",
        "type": "chat",
        "status": "active",
        "requests": 9203,
        "latency": 189.0,
        "model": "llama3.1",
        "system_prompt": "You are a general support bot.",
        "skills": []
    },
    {
        "id": "agent-3",
        "name": "Search Assistant",
        "type": "search",
        "status": "inactive",
        "requests": 5021,
        "latency": 156.0,
        "model": "gpt-4o",
        "system_prompt": "You are a web search helper.",
        "skills": []
    }
]


def _load_agents() -> List[dict]:
    if not _AGENTS_PATH.exists():
        _save_agents(DEFAULT_AGENTS)
        return DEFAULT_AGENTS
    try:
        return json.loads(_AGENTS_PATH.read_text("utf-8"))
    except Exception:
        return DEFAULT_AGENTS


def _save_agents(agents: List[dict]) -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    _AGENTS_PATH.write_text(json.dumps(agents, indent=2), encoding="utf-8")


@router.get("", response_model=List[AgentResponse])
async def list_agents():
    """List all agents"""
    return _load_agents()


@router.get("/skills")
async def list_skills():
    """List available skills from the skills store"""
    store = SkillsStore(_SKILLS_DIR)
    return store.list()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str):
    """Get specific agent"""
    agents = _load_agents()
    agent = next((a for a in agents if a["id"] == agent_id), None)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(agent: AgentCreate):
    """Create new agent"""
    agents = _load_agents()
    new_agent = {
        "id": f"agent-{len(agents) + 1}",
        **agent.dict(),
        "requests": 0,
        "latency": 0.0
    }
    agents.append(new_agent)
    _save_agents(agents)
    return new_agent

