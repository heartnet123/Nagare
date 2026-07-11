import uuid

from fastapi import APIRouter, HTTPException

from models.settings import (
    ApiKeyCreate,
    ApiKeyFullResponse,
    ApiKeyResponse,
    NotificationPreferences,
    ThemeSettings,
    UserPreferences,
)
from models.user import UserProfile

router = APIRouter(prefix="/api/settings", tags=["settings"])

MOCK_PROFILE = {
    "id": "user-1",
    "username": "admin",
    "display_name": "Administrator",
    "avatar_url": None,
    "bio": "System administrator",
    "email": "admin@nagare.ai",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": None,
}

MOCK_API_KEYS = [
    {
        "id": "key-1",
        "name": "Production API Key",
        "description": "Main production key",
        "key_prefix": "sk-nag-",
        "created_at": "2024-06-01T00:00:00Z",
        "expires_at": "2025-06-01T00:00:00Z",
        "last_used_at": "2024-07-01T12:00:00Z",
        "is_active": True,
    }
]

MOCK_NOTIFICATIONS = {
    "email_notifications": True,
    "in_app_notifications": True,
    "agent_alerts": True,
    "weekly_digest": False,
    "security_alerts": True,
}

MOCK_THEME = {
    "theme": "system",
    "accent_color": None,
    "font_size": "medium",
}

MOCK_PREFERENCES = {
    "notifications": MOCK_NOTIFICATIONS,
    "theme": MOCK_THEME,
    "language": "en",
    "timezone": "UTC",
}


@router.get("/profile", response_model=UserProfile)
async def get_profile():
    return MOCK_PROFILE


@router.put("/profile", response_model=UserProfile)
async def update_profile(profile: dict):
    MOCK_PROFILE.update(profile)
    MOCK_PROFILE["updated_at"] = "2024-07-09T00:00:00Z"
    return MOCK_PROFILE


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys():
    return MOCK_API_KEYS


@router.post("/api-keys", response_model=ApiKeyFullResponse, status_code=201)
async def create_api_key(key: ApiKeyCreate):
    new_key = {
        "id": f"key-{uuid.uuid4().hex[:8]}",
        "name": key.name,
        "description": key.description,
        "key_prefix": "sk-nag-",
        "key": f"sk-nag-{uuid.uuid4().hex}",
        "created_at": "2024-07-09T00:00:00Z",
        "expires_at": key.expires_at,
        "last_used_at": None,
        "is_active": True,
    }
    MOCK_API_KEYS.append(new_key)
    return new_key


@router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(key_id: str):
    for key in MOCK_API_KEYS:
        if key["id"] == key_id:
            key["is_active"] = False
            return {"message": "Key revoked"}
    raise HTTPException(status_code=404, detail="API key not found")


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str):
    global MOCK_API_KEYS
    original_len = len(MOCK_API_KEYS)
    MOCK_API_KEYS = [key for key in MOCK_API_KEYS if key["id"] != key_id]
    if len(MOCK_API_KEYS) == original_len:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "Key deleted"}


@router.get("/notifications", response_model=NotificationPreferences)
async def get_notifications():
    return MOCK_NOTIFICATIONS


@router.put("/notifications", response_model=NotificationPreferences)
async def update_notifications(prefs: dict):
    MOCK_NOTIFICATIONS.update(prefs)
    return MOCK_NOTIFICATIONS


@router.get("/theme", response_model=ThemeSettings)
async def get_theme():
    return MOCK_THEME


@router.put("/theme", response_model=ThemeSettings)
async def update_theme(theme: dict):
    MOCK_THEME.update(theme)
    return MOCK_THEME


@router.get("/preferences", response_model=UserPreferences)
async def get_preferences():
    return MOCK_PREFERENCES


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(prefs: dict):
    if "notifications" in prefs:
        MOCK_PREFERENCES["notifications"].update(prefs["notifications"])
    if "theme" in prefs:
        MOCK_PREFERENCES["theme"].update(prefs["theme"])
    for key in ["language", "timezone"]:
        if key in prefs:
            MOCK_PREFERENCES[key] = prefs[key]
    return MOCK_PREFERENCES
