from fastapi import APIRouter, HTTPException
from typing import List
from models.dataset import DatasetResponse, DatasetCreate

router = APIRouter(prefix="/api/datasets", tags=["datasets"])

MOCK_DATASETS = [
    {"id": "ds-1", "name": "legal-docs", "format": "jsonl", "rows": 240, "uploaded": "2024-06-15"},
    {"id": "ds-2", "name": "support-tickets", "format": "csv", "rows": 512, "uploaded": "2024-06-20"},
    {"id": "ds-3", "name": "product-manuals", "format": "json", "rows": 180, "uploaded": "2024-06-25"}
]


@router.get("", response_model=List[DatasetResponse])
async def list_datasets():
    """List all datasets"""
    return MOCK_DATASETS


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: str):
    """Get specific dataset"""
    ds = next((d for d in MOCK_DATASETS if d["id"] == dataset_id), None)
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return ds


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(dataset: DatasetCreate):
    """Upload new dataset"""
    new_ds = {
        "id": f"ds-{len(MOCK_DATASETS) + 1}",
        **dataset.dict(),
        "uploaded": "2024-07-02"
    }
    MOCK_DATASETS.append(new_ds)
    return new_ds
