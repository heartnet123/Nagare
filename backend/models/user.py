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


class UserProfile(BaseModel):
    id: str
    username: str
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    email: str | None = None
    created_at: str
    updated_at: str | None = None
