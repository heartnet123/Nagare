from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from services.data import connect_db
from middleware.auth import get_current_user_from_cookie


def test_schema_has_inbox_decisions(tmp_path):
    with connect_db(tmp_path) as db:
        assert db.execute("select name from sqlite_master where name = 'inbox_decisions'").fetchone()


def test_inbox_decisions_real_flow(monkeypatch, tmp_path):
    monkeypatch.setattr("services.data.default_data_dir", lambda: tmp_path)
    test_user = {"id": "user-test-1", "username": "alex"}
    with connect_db(tmp_path) as db:
        db.execute("insert into users (id, username, password_hash, created_at) values (?, ?, ?, ?)",
                   (test_user["id"], test_user["username"], "hash", "2025-01-01T00:00:00Z"))
        db.commit()
    app.dependency_overrides[get_current_user_from_cookie] = lambda: test_user

    try:
        client = TestClient(app)

        # 1. Initially 0 decisions (Empty state)
        res_empty = client.get("/api/inbox/decisions")
        assert res_empty.status_code == 200
        assert res_empty.json() == []

        # 2. Create decision (mutation)
        create_payload = {
            "title": "Approve campaign brief",
            "subtitle": "Launch-ready campaign for Q2 product release.",
            "priority": "high",
            "agent_name": "Nova",
            "agent_role": "Marketing agent",
            "project": "Q2 launch campaign",
            "summary": "Nova prepared full brief.",
            "key_rationale": ["Aligned with product positioning"],
            "potential_risks": ["Higher-than-expected CPC"],
            "alternatives": [
                {"id": "opt-a", "label": "Option A", "name": "Full funnel", "recommended": True}
            ],
            "files": [
                {"name": "Brief.pdf", "size": "2.4 MB", "type": "pdf"}
            ]
        }
        res_create = client.post("/api/inbox/decisions", json=create_payload)
        assert res_create.status_code == 201
        created = res_create.json()
        assert created["title"] == "Approve campaign brief"
        decision_id = created["id"]

        # 3. List now has 1 item (Data state)
        res_list = client.get("/api/inbox/decisions")
        assert len(res_list.json()) == 1

        # 4. Patch selected alternative
        res_patch = client.patch(f"/api/inbox/decisions/{decision_id}", json={"selected_alternative": "opt-b"})
        assert res_patch.status_code == 200
        assert res_patch.json()["selected_alternative"] == "opt-b"

        # 5. Stats live calculation
        res_stats = client.get("/api/inbox/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["pending_count"] == 1
        assert stats["urgent_count"] == 1

        # 6. Approve mutation
        res_approve = client.post(f"/api/inbox/decisions/{decision_id}/approve")
        assert res_approve.status_code == 200
        assert res_approve.json()["new_status"] == "approved"

        # Pending now 0 (transitions to empty for pending filter)
        res_pending = client.get("/api/inbox/decisions?filter=all")
        assert len(res_pending.json()) == 0

        # Approved filter has 1
        res_approved = client.get("/api/inbox/decisions?filter=approved")
        assert len(res_approved.json()) == 1

        # 7. Delete decision
        res_del = client.delete(f"/api/inbox/decisions/{decision_id}")
        assert res_del.status_code == 200
        res_final = client.get("/api/inbox/decisions")
        assert len(res_final.json()) == 0
    finally:
        app.dependency_overrides.pop(get_current_user_from_cookie, None)
