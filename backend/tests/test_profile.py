import pytest
from fastapi.testclient import TestClient
from main import app
from services.data import connect_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def run_around_tests():
    client.post("/api/profile/reset")
    yield
    client.post("/api/profile/reset")


def test_get_profile():
    res = client.get("/api/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Alex Chen"
    assert data["email"] == "alex@nagareos.com"
    assert data["role"] == "Workspace owner"
    assert len(data["connected_accounts"]) >= 4
    assert data["completion_percentage"] == 80


def test_update_profile():
    res = client.put("/api/profile", json={
        "full_name": "Alexander Chen",
        "bio": "Updated bio text here"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["full_name"] == "Alexander Chen"
    assert data["bio"] == "Updated bio text here"
    # Verify recent activity got logged
    assert any("Updated your profile" in act["title"] for act in data["recent_activity"])

    # Revert back
    client.put("/api/profile", json={"full_name": "Alex Chen", "bio": "Building AI tools for a more productive and creative world."})


def test_update_notifications():
    res = client.put("/api/profile/notifications", json={
        "weekly_digest": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["weekly_digest"] is False

    # Restore
    client.put("/api/profile/notifications", json={"weekly_digest": True})


def test_connected_accounts_lifecycle():
    # Add new account
    res = client.post("/api/profile/connected-accounts", json={
        "provider": "figma",
        "account_name": "alex@nagareos.com"
    })
    assert res.status_code == 200
    data = res.json()
    assert any(a["provider"] == "figma" for a in data["connected_accounts"])

    # Delete account
    res = client.delete("/api/profile/connected-accounts/figma")
    assert res.status_code == 200
    data = res.json()
    assert not any(a["provider"] == "figma" for a in data["connected_accounts"])


def test_toggle_checklist():
    res = client.post("/api/profile/toggle-checklist/account")
    assert res.status_code == 200
    data = res.json()
    acc_item = next(i for i in data["completion_items"] if i["id"] == "account")
    assert acc_item["completed"] is True
    assert data["completion_percentage"] == 100

    # Toggle back
    res = client.post("/api/profile/toggle-checklist/account")
    assert res.status_code == 200
    data = res.json()
    acc_item = next(i for i in data["completion_items"] if i["id"] == "account")
    assert acc_item["completed"] is False
    assert data["completion_percentage"] == 75
