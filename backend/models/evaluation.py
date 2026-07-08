from pydantic import BaseModel, Field


class EvaluationRunBase(BaseModel):
    dataset: str
    cases: int
    faithfulness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    precision: float = Field(ge=0.0, le=1.0)
    status: str  # "passed" | "failed" | "running"


class EvaluationRunCreate(EvaluationRunBase):
    pass


class EvaluationRunResponse(EvaluationRunBase):
    id: str
    time: str

    class Config:
        from_attributes = True
