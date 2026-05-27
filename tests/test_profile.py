"""Sprint 2 — Profile CRUD 測試（A1-8）"""

import pytest
from tests.conftest import auth_header


class TestProfileCRUD:
    def test_create_profile(self, client, auth_tokens):
        resp = client.post(
            "/api/auth/profiles",
            headers=auth_header(auth_tokens["access"]),
            json={"name": "本人", "relationship": "本人"},
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["success"] is True
        assert data["profile"]["name"] == "本人"
        assert data["profile"]["is_default"] is True  # 第一筆自動為 default

    def test_list_profiles(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        client.post("/api/auth/profiles", headers=hdr, json={"name": "本人"})
        client.post(
            "/api/auth/profiles",
            headers=hdr,
            json={"name": "爸爸", "relationship": "父親"},
        )

        resp = client.get("/api/auth/profiles", headers=hdr)
        assert resp.status_code == 200
        profiles = resp.get_json()["profiles"]
        assert len(profiles) == 2

    def test_update_profile(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        create_resp = client.post(
            "/api/auth/profiles", headers=hdr, json={"name": "本人"}
        )
        pid = create_resp.get_json()["profile"]["id"]

        resp = client.put(
            f"/api/auth/profiles/{pid}",
            headers=hdr,
            json={"name": "更新名稱", "birth_date": "2000-01-15"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["profile"]["name"] == "更新名稱"
        assert resp.get_json()["profile"]["birth_date"] == "2000-01-15"

    def test_delete_profile(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        create_resp = client.post(
            "/api/auth/profiles", headers=hdr, json={"name": "臨時"}
        )
        pid = create_resp.get_json()["profile"]["id"]

        resp = client.delete(f"/api/auth/profiles/{pid}", headers=hdr)
        assert resp.status_code == 200

        # 確認已刪除
        resp2 = client.get("/api/auth/profiles", headers=hdr)
        ids = [p["id"] for p in resp2.get_json()["profiles"]]
        assert pid not in ids

    def test_update_nonexistent_profile_404(self, client, auth_tokens):
        resp = client.put(
            "/api/auth/profiles/99999",
            headers=auth_header(auth_tokens["access"]),
            json={"name": "x"},
        )
        assert resp.status_code == 404

    def test_create_profile_missing_name(self, client, auth_tokens):
        resp = client.post(
            "/api/auth/profiles",
            headers=auth_header(auth_tokens["access"]),
            json={"relationship": "父親"},
        )
        assert resp.status_code == 400

    def test_create_profile_no_auth(self, client):
        resp = client.post("/api/auth/profiles", json={"name": "x"})
        assert resp.status_code == 401
