from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    """Request body for user login."""
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
