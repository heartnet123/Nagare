from pydantic import BaseModel


class LogEntry(BaseModel):
    id: str
    timestamp: str
    level: str  # "info" | "warning" | "error"
    service: str
    message: str
