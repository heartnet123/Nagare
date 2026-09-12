from pydantic import BaseModel
from typing import Optional, List


class ConnectedAccount(BaseModel):
    provider: str
    account_name: str
    status: str = "connected"


class CompletionItem(BaseModel):
    id: str
    label: str
    completed: bool


class ActivityItem(BaseModel):
    id: str
    title: str
    time_ago: str
    type: str = "profile"


class ProfileData(BaseModel):
    id: str = "usr_8f2e9c1a"
    full_name: str = "Alex Chen"
    role: str = "Workspace owner"
    email: str = "alex@nagareos.com"
    phone: str = "+1 (415) 555-0123"
    location: str = "San Francisco, CA, USA"
    company: str = "NagareOS"
    bio: str = "Building AI tools for a more productive and creative world."
    avatar_url: str = "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=256&q=80"
    
    # Work preferences
    default_workspace: str = "Personal workspace"
    preferred_language: str = "English (US)"
    timezone: str = "Pacific Time (PST)"
    timezone_utc: str = "UTC-8"
    working_hours: str = "9:00 AM – 6:00 PM Mon – Fri"
    
    # Notifications
    email_notifications: bool = True
    task_updates: bool = True
    approval_requests: bool = True
    weekly_digest: bool = True
    
    # Security
    password_last_changed: str = "Last changed 3 months ago"
    two_factor_enabled: bool = True
    active_sessions: int = 3
    recent_login: str = "Apr 27, 2025, 11:24 AM San Francisco, CA"
    
    # Connected accounts
    connected_accounts: List[ConnectedAccount] = [
        ConnectedAccount(provider="google", account_name="alex@nagareos.com", status="connected"),
        ConnectedAccount(provider="slack", account_name="alexchen", status="connected"),
        ConnectedAccount(provider="github", account_name="alexchen", status="connected"),
        ConnectedAccount(provider="notion", account_name="alex@nagareos.com", status="connected")
    ]
    
    # Profile completion
    completion_percentage: int = 80
    completion_items: List[CompletionItem] = [
        CompletionItem(id="photo", label="Add profile photo", completed=True),
        CompletionItem(id="basic", label="Add basic information", completed=True),
        CompletionItem(id="preferences", label="Set your preferences", completed=True),
        CompletionItem(id="account", label="Connect at least one account", completed=False)
    ]
    
    # Recent activity
    recent_activity: List[ActivityItem] = [
        ActivityItem(id="act-1", title="Updated your profile", time_ago="2 hours ago", type="profile"),
        ActivityItem(id="act-2", title="Connected Notion account", time_ago="1 day ago", type="notion"),
        ActivityItem(id="act-3", title="Changed notification settings", time_ago="3 days ago", type="settings"),
        ActivityItem(id="act-4", title="Signed in from a new device", time_ago="Apr 27, 2025", type="security")
    ]
    
    # Account
    plan: str = "Pro"
    member_since: str = "Jan 12, 2024"
    account_id: str = "usr_8f2e9c1a"


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    default_workspace: Optional[str] = None
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    timezone_utc: Optional[str] = None
    working_hours: Optional[str] = None


class NotificationUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    task_updates: Optional[bool] = None
    approval_requests: Optional[bool] = None
    weekly_digest: Optional[bool] = None


class ConnectedAccountCreate(BaseModel):
    provider: str
    account_name: str
