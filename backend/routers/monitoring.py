from fastapi import APIRouter
from typing import List
from models.monitoring import MetricResponse

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

MOCK_METRICS = [
    {"timestamp": "2024-07-02T10:00:00Z", "latency_p50": 245.0, "latency_p99": 892.0, "error_rate": 0.012, "throughput": 1247},
    {"timestamp": "2024-07-02T10:05:00Z", "latency_p50": 238.0, "latency_p99": 867.0, "error_rate": 0.008, "throughput": 1312},
    {"timestamp": "2024-07-02T10:10:00Z", "latency_p50": 251.0, "latency_p99": 901.0, "error_rate": 0.015, "throughput": 1189}
]


@router.get("/metrics", response_model=List[MetricResponse])
async def get_metrics():
    """Get monitoring metrics"""
    return MOCK_METRICS
