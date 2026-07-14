from pydantic import BaseModel, Field, HttpUrl

class RagConnectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    base_url: HttpUrl
    model: str = Field(min_length=1, max_length=200)
    api_key: str = Field(min_length=1, max_length=4096)

class RagConnectionResponse(BaseModel):
    id: str
    name: str
    base_url: str
    model: str
    api_key_set: bool
    created_at: str
    updated_at: str

class RagConnectionTest(BaseModel):
    base_url: HttpUrl
    model: str = Field(min_length=1, max_length=200)
    api_key: str = Field(min_length=1, max_length=4096)

class RagConnectionTestResponse(BaseModel):
    ok: bool
    message: str
