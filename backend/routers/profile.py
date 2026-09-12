import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from models.profile import (
    ProfileData,
    ProfileUpdate,
    NotificationUpdate,
    ConnectedAccountCreate,
    ConnectedAccount,
    CompletionItem,
    ActivityItem,
)
from services.data import connect_db

router = APIRouter(prefix="/api/profile", tags=["profile"])


def _row_to_profile(row) -> ProfileData:
    connected = [ConnectedAccount(**x) for x in json.loads(row["connected_accounts"])]
    items = [CompletionItem(**x) for x in json.loads(row["completion_items"])]
    activities = [ActivityItem(**x) for x in json.loads(row["recent_activity"])]

    return ProfileData(
        id=row["id"],
        full_name=row["full_name"],
        role=row["role"],
        email=row["email"],
        phone=row["phone"],
        location=row["location"],
        company=row["company"],
        bio=row["bio"],
        avatar_url=row["avatar_url"],
        default_workspace=row["default_workspace"],
        preferred_language=row["preferred_language"],
        timezone=row["timezone"],
        timezone_utc=row["timezone_utc"],
        working_hours=row["working_hours"],
        email_notifications=bool(row["email_notifications"]),
        task_updates=bool(row["task_updates"]),
        approval_requests=bool(row["approval_requests"]),
        weekly_digest=bool(row["weekly_digest"]),
        password_last_changed=row["password_last_changed"],
        two_factor_enabled=bool(row["two_factor_enabled"]),
        active_sessions=row["active_sessions"],
        recent_login=row["recent_login"],
        connected_accounts=connected,
        completion_percentage=row["completion_percentage"],
        completion_items=items,
        recent_activity=activities,
        plan=row["plan"],
        member_since=row["member_since"],
        account_id=row["account_id"],
    )


@router.get("", response_model=ProfileData)
async def get_profile():
    conn = connect_db()
    try:
        row = conn.execute("SELECT * FROM user_profiles LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")
        return _row_to_profile(row)
    finally:
        conn.close()


@router.put("", response_model=ProfileData)
async def update_profile(update: ProfileUpdate):
    conn = connect_db()
    try:
        row = conn.execute("SELECT * FROM user_profiles LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")

        fields = update.model_dump(exclude_unset=True)
        if not fields:
            return _row_to_profile(row)

        now = datetime.now(timezone.utc).isoformat()
        fields["updated_at"] = now

        # Add recent activity record for profile update
        activities = json.loads(row["recent_activity"])
        activities.insert(0, {
            "id": f"act-{len(activities)+1}",
            "title": "Updated your profile",
            "time_ago": "Just now",
            "type": "profile"
        })
        fields["recent_activity"] = json.dumps(activities[:8])

        set_clause = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [row["id"]]

        conn.execute(f"UPDATE user_profiles SET {set_clause} WHERE id = ?", values)
        conn.commit()

        updated_row = conn.execute("SELECT * FROM user_profiles WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_profile(updated_row)
    finally:
        conn.close()


@router.put("/notifications", response_model=ProfileData)
async def update_notifications(update: NotificationUpdate):
    conn = connect_db()
    try:
        row = conn.execute("SELECT * FROM user_profiles LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")

        fields = update.model_dump(exclude_unset=True)
        if not fields:
            return _row_to_profile(row)

        now = datetime.now(timezone.utc).isoformat()
        db_fields = {}
        for k, v in fields.items():
            db_fields[k] = 1 if v else 0
        db_fields["updated_at"] = now

        activities = json.loads(row["recent_activity"])
        activities.insert(0, {
            "id": f"act-{len(activities)+1}",
            "title": "Changed notification settings",
            "time_ago": "Just now",
            "type": "settings"
        })
        db_fields["recent_activity"] = json.dumps(activities[:8])

        set_clause = ", ".join(f"{k} = ?" for k in db_fields.keys())
        values = list(db_fields.values()) + [row["id"]]

        conn.execute(f"UPDATE user_profiles SET {set_clause} WHERE id = ?", values)
        conn.commit()

        updated_row = conn.execute("SELECT * FROM user_profiles WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_profile(updated_row)
    finally:
        conn.close()


@router.post("/connected-accounts", response_model=ProfileData)
async def add_connected_account(account: ConnectedAccountCreate):
    conn = connect_db()
    try:
        row = conn.execute("SELECT * FROM user_profiles LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")

        accounts = json.loads(row["connected_accounts"])
        # Remove existing if same provider, then add
        accounts = [a for a in accounts if a["provider"].lower() != account.provider.lower()]
        accounts.append({
            "provider": account.provider.lower(),
            "account_name": account.account_name,
            "status": "connected"
        })

        activities = json.loads(row["recent_activity"])
        activities.insert(0, {
            "id": f"act-{len(activities)+1}",
            "title": f"Connected {account.provider.capitalize()} account",
            "time_ago": "Just now",
            "type": account.provider.lower()
        })

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """UPDATE user_profiles SET
               connected_accounts = ?, recent_activity = ?, updated_at = ?
               WHERE id = ?""",
            (json.dumps(accounts), json.dumps(activities[:8]), now, row["id"])
        )
        conn.commit()

        updated_row = conn.execute("SELECT * FROM user_profiles WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_profile(updated_row)
    finally:
        conn.close()


@router.delete("/connected-accounts/{provider}", response_model=ProfileData)
async def delete_connected_account(provider: str):
    conn = connect_db()
    try:
        row = conn.execute("SELECT * FROM user_profiles LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")

        accounts = json.loads(row["connected_accounts"])
        accounts = [a for a in accounts if a["provider"].lower() != provider.lower()]

        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """UPDATE user_profiles SET
               connected_accounts = ?, updated_at = ?
               WHERE id = ?""",
            (json.dumps(accounts), now, row["id"])
        )
        conn.commit()

        updated_row = conn.execute("SELECT * FROM user_profiles WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_profile(updated_row)
    finally:
        conn.close()


@router.post("/toggle-checklist/{item_id}", response_model=ProfileData)
async def toggle_checklist(item_id: str):
    conn = connect_db()
    try:
        row = conn.execute("SELECT * FROM user_profiles LIMIT 1").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Profile not found")

        items = json.loads(row["completion_items"])
        found = False
        for it in items:
            if it["id"] == item_id:
                it["completed"] = not it["completed"]
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail=f"Checklist item '{item_id}' not found")

        completed_cnt = sum(1 for it in items if it["completed"])
        pct = int((completed_cnt / len(items)) * 100) if items else 100
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            "UPDATE user_profiles SET completion_items = ?, completion_percentage = ?, updated_at = ? WHERE id = ?",
            (json.dumps(items), pct, now, row["id"])
        )
        conn.commit()

        updated_row = conn.execute("SELECT * FROM user_profiles WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_profile(updated_row)
    finally:
        conn.close()


@router.post("/reset", response_model=ProfileData)
async def reset_profile():
    conn = connect_db()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute("DELETE FROM user_profiles")
        conn.execute('''
            INSERT INTO user_profiles (
                id, full_name, role, email, phone, location, company, bio, avatar_url,
                default_workspace, preferred_language, timezone, timezone_utc, working_hours,
                email_notifications, task_updates, approval_requests, weekly_digest,
                password_last_changed, two_factor_enabled, active_sessions, recent_login,
                connected_accounts, completion_percentage, completion_items, recent_activity,
                plan, member_since, account_id, created_at, updated_at
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        ''', (
            "usr_8f2e9c1a", "Alex Chen", "Workspace owner", "alex@nagareos.com",
            "+1 (415) 555-0123", "San Francisco, CA, USA", "NagareOS",
            "Building AI tools for a more productive and creative world.",
            "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=256&q=80",
            "Personal workspace", "English (US)", "Pacific Time (PST)", "UTC-8",
            "9:00 AM – 6:00 PM Mon – Fri",
            1, 1, 1, 1,
            "Last changed 3 months ago", 1, 3, "Apr 27, 2025, 11:24 AM San Francisco, CA",
            json.dumps([
                {"provider": "google", "account_name": "alex@nagareos.com", "status": "connected"},
                {"provider": "slack", "account_name": "alexchen", "status": "connected"},
                {"provider": "github", "account_name": "alexchen", "status": "connected"},
                {"provider": "notion", "account_name": "alex@nagareos.com", "status": "connected"}
            ]),
            80,
            json.dumps([
                {"id": "photo", "label": "Add profile photo", "completed": True},
                {"id": "basic", "label": "Add basic information", "completed": True},
                {"id": "preferences", "label": "Set your preferences", "completed": True},
                {"id": "account", "label": "Connect at least one account", "completed": False}
            ]),
            json.dumps([
                {"id": "act-1", "title": "Updated your profile", "time_ago": "2 hours ago", "type": "profile"},
                {"id": "act-2", "title": "Connected Notion account", "time_ago": "1 day ago", "type": "notion"},
                {"id": "act-3", "title": "Changed notification settings", "time_ago": "3 days ago", "type": "settings"},
                {"id": "act-4", "title": "Signed in from a new device", "time_ago": "Apr 27, 2025", "type": "security"}
            ]),
            "Pro", "Jan 12, 2024", "usr_8f2e9c1a", now, now
        ))
        conn.commit()
        row = conn.execute("SELECT * FROM user_profiles LIMIT 1").fetchone()
        return _row_to_profile(row)
    finally:
        conn.close()
