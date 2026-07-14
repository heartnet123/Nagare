from typing import Literal

from pydantic import BaseModel


class ApiKeyCreate(BaseModel):
    name: str
    description: str | None = None
    expires_at: str | None = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    key_prefix: str
    created_at: str
    expires_at: str | None = None
    last_used_at: str | None = None
    is_active: bool


class ApiKeyFullResponse(ApiKeyResponse):
    key: str


class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    in_app_notifications: bool = True
    agent_alerts: bool = True
    weekly_digest: bool = False
    security_alerts: bool = True


class ThemeSettings(BaseModel):
    theme: Literal["light", "dark", "system"] = "system"
    accent_color: str | None = None
    font_size: Literal["small", "medium", "large"] = "medium"


class UserPreferences(BaseModel):
    notifications: NotificationPreferences
    theme: ThemeSettings
    language: str = "en"
    timezone: str = "UTC"
