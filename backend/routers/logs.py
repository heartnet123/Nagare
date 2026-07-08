from fastapi import APIRouter
from typing import List
from models.log import LogEntry

router = APIRouter(prefix="/api/logs", tags=["logs"])

MOCK_LOGS = [
    {"id": "log-1", "timestamp": "2024-07-02T10:23:45Z", "level": "info", "service": "rag-service", "message": "Query processed successfully"},
    {"id": "log-2", "timestamp": "2024-07-02T10:22:10Z", "level": "error", "service": "vector-db", "message": "Connection timeout"},
    {"id": "log-3", "timestamp": "2024-07-02T10:20:33Z", "level": "warning", "service": "api-gateway", "message": "High latency detected"},
    {"id": "log-4", "timestamp": "2024-07-02T10:18:15Z", "level": "info", "service": "auth-service", "message": "User authenticated"}
]


@router.get("", response_model=List[LogEntry])
async def get_logs():
    """Get system logs"""
    return MOCK_LOGS
