from pydantic import BaseModel


class MetricResponse(BaseModel):
    timestamp: str
    latency_p50: float
    latency_p99: float
    error_rate: float
    throughput: int
