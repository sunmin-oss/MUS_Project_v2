"""Sprint 3 — Medications CRUD 測試（S1-1）"""

import pytest
from tests.conftest import auth_header


def _create_profile(client, token):
    """建立 profile 並回傳 id"""
    resp = client.post(
        "/api/auth/profiles",
        headers=auth_header(token),
        json={"name": "本人", "relationship": "本人"},
    )
    return resp.get_json()["profile"]["id"]


class TestMedicationsCRUD:
    def test_create_medication(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        pid = _create_profile(client, auth_tokens["access"])
        resp = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "普拿疼",
                "profile_id": pid,
                "dosage": "1",
                "unit": "顆",
                "frequency": "tid",
                "start_date": "2026-05-27",
                "schedules": [
                    {"time_slot": "morning", "scheduled_time": "08:00", "dose_qty": 1},
                    {"time_slot": "noon", "scheduled_time": "12:00", "dose_qty": 1},
                    {"time_slot": "evening", "scheduled_time": "18:00", "dose_qty": 1},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["medication"]["name"] == "普拿疼"
        assert len(data["medication"]["schedules"]) == 3

    def test_list_medications(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        pid = _create_profile(client, auth_tokens["access"])
        client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "藥A",
                "profile_id": pid,
                "start_date": "2026-05-27",
            },
        )
        client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "藥B",
                "profile_id": pid,
                "start_date": "2026-05-27",
            },
        )
        resp = client.get("/api/user/medications", headers=hdr)
        assert resp.status_code == 200
        assert len(resp.get_json()["medications"]) >= 2

    def test_update_medication(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        pid = _create_profile(client, auth_tokens["access"])
        create = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "原名",
                "profile_id": pid,
                "start_date": "2026-05-27",
            },
        )
        mid = create.get_json()["medication"]["id"]
        resp = client.put(
            f"/api/user/medications/{mid}",
            headers=hdr,
            json={
                "name": "新名",
                "stock_qty": 30,
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["medication"]["name"] == "新名"
        assert resp.get_json()["medication"]["stock_qty"] == 30

    def test_delete_medication(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        pid = _create_profile(client, auth_tokens["access"])
        create = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "待刪",
                "profile_id": pid,
                "start_date": "2026-05-27",
            },
        )
        mid = create.get_json()["medication"]["id"]
        resp = client.delete(f"/api/user/medications/{mid}", headers=hdr)
        assert resp.status_code == 200

    def test_create_missing_profile(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        resp = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "x",
                "profile_id": 99999,
                "start_date": "2026-05-27",
            },
        )
        assert resp.status_code == 404

    def test_create_missing_name(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        pid = _create_profile(client, auth_tokens["access"])
        resp = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "profile_id": pid,
                "start_date": "2026-05-27",
            },
        )
        assert resp.status_code == 400

    def test_no_auth(self, client):
        resp = client.get("/api/user/medications")
        assert resp.status_code == 401
