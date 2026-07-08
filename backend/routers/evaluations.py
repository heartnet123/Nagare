from fastapi import APIRouter, HTTPException
from typing import List
from models.evaluation import EvaluationRunResponse, EvaluationRunCreate

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])

# Mock data (replace with DB calls in F2)
MOCK_RUNS = [
    {"id": "run-8842", "dataset": "legal-docs", "cases": 240, "faithfulness": 0.91, "relevance": 0.88, "precision": 0.86, "status": "passed", "time": "2 min ago"},
    {"id": "run-8841", "dataset": "support-tickets", "cases": 512, "faithfulness": 0.87, "relevance": 0.9, "precision": 0.83, "status": "passed", "time": "1 hour ago"},
    {"id": "run-8840", "dataset": "product-manuals", "cases": 180, "faithfulness": 0.79, "relevance": 0.81, "precision": 0.74, "status": "failed", "time": "3 hours ago"},
    {"id": "run-8839", "dataset": "research-papers", "cases": 96, "faithfulness": 0.93, "relevance": 0.89, "precision": 0.88, "status": "passed", "time": "5 hours ago"},
    {"id": "run-8838", "dataset": "legal-docs", "cases": 240, "faithfulness": 0.9, "relevance": 0.86, "precision": 0.85, "status": "passed", "time": "Yesterday"},
    {"id": "run-8837", "dataset": "onboarding", "cases": 64, "faithfulness": 0.72, "relevance": 0.7, "precision": 0.68, "status": "failed", "time": "Yesterday"}
]


@router.get("/runs", response_model=List[EvaluationRunResponse])
async def list_evaluation_runs():
    """List all evaluation runs"""
    return MOCK_RUNS


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run(run_id: str):
    """Get specific evaluation run"""
    run = next((r for r in MOCK_RUNS if r["id"] == run_id), None)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.post("/runs", response_model=EvaluationRunResponse, status_code=201)
async def create_evaluation_run(run: EvaluationRunCreate):
    """Create new evaluation run"""
    new_run = {
        "id": f"run-{len(MOCK_RUNS) + 1000}",
        **run.dict(),
        "time": "just now"
    }
    MOCK_RUNS.insert(0, new_run)
    return new_run
