from pydantic import BaseModel


class DatasetBase(BaseModel):
    name: str
    format: str  # "csv" | "json" | "jsonl"
    rows: int


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(DatasetBase):
    id: str
    uploaded: str

    class Config:
        from_attributes = True
