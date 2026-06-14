"""Sprint 3 — 服藥紀錄 + Push Token 測試（S1-7 / S1-2）"""

import pytest
from tests.conftest import auth_header


def _setup_med(client, token):
    """建立 profile + medication 並回傳 (profile_id, medication_id)"""
    hdr = auth_header(token)
    p = client.post("/api/auth/profiles", headers=hdr, json={"name": "本人"})
    pid = p.get_json()["profile"]["id"]
    m = client.post(
        "/api/user/medications",
        headers=hdr,
        json={
            "name": "測試藥",
            "profile_id": pid,
            "start_date": "2026-05-27",
            "stock_qty": 10,
        },
    )
    mid = m.get_json()["medication"]["id"]
    return pid, mid


class TestAdherence:
    def test_log_taken(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        _, mid = _setup_med(client, auth_tokens["access"])
        resp = client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "taken",
                "scheduled_date": "2026-05-27",
            },
        )
        assert resp.status_code == 201
        assert resp.get_json()["log"]["status"] == "taken"

    def test_log_skipped(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        _, mid = _setup_med(client, auth_tokens["access"])
        resp = client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "skipped",
                "scheduled_date": "2026-05-27",
            },
        )
        assert resp.status_code == 201

    def test_stock_decrements(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        _, mid = _setup_med(client, auth_tokens["access"])
        client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "taken",
                "scheduled_date": "2026-05-27",
            },
        )
        med = client.get(f"/api/user/medications/{mid}", headers=hdr)
        assert med.get_json()["medication"]["stock_qty"] == 9

    def test_list_adherence(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        _, mid = _setup_med(client, auth_tokens["access"])
        client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "taken",
                "scheduled_date": "2026-05-27",
            },
        )
        resp = client.get(
            "/api/user/adherence?start=2026-05-01&end=2026-05-31", headers=hdr
        )
        assert resp.status_code == 200
        assert len(resp.get_json()["logs"]) >= 1

    def test_adherence_stats(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        _, mid = _setup_med(client, auth_tokens["access"])
        client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "taken",
                "scheduled_date": "2026-05-27",
            },
        )
        client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "skipped",
                "scheduled_date": "2026-05-26",
            },
        )
        resp = client.get("/api/user/adherence/stats?days=30", headers=hdr)
        data = resp.get_json()["stats"]
        assert data["total"] == 2
        assert data["taken"] == 1
        assert data["skipped"] == 1

    def test_invalid_status(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        _, mid = _setup_med(client, auth_tokens["access"])
        resp = client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "invalid",
            },
        )
        assert resp.status_code == 400


class TestPushToken:
    def test_register_token(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        resp = client.post(
            "/api/user/push-token",
            headers=hdr,
            json={
                "token": "fake-apns-token-12345",
                "platform": "ios",
            },
        )
        assert resp.status_code == 200

    def test_register_token_missing_platform(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        resp = client.post(
            "/api/user/push-token",
            headers=hdr,
            json={
                "token": "abc123",
            },
        )
        assert resp.status_code == 400

    def test_unregister_token(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        client.post(
            "/api/user/push-token",
            headers=hdr,
            json={
                "token": "token-to-remove",
                "platform": "ios",
            },
        )
        resp = client.delete(
            "/api/user/push-token",
            headers=hdr,
            json={
                "token": "token-to-remove",
            },
        )
        assert resp.status_code == 200
