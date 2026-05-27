"""Sprint 2 — JWT 登入 / 刷新 / 登出 測試（A1-3）"""

import uuid
import pytest
from tests.conftest import auth_header


def _unique_user():
    return f"jwt_{uuid.uuid4().hex[:8]}"


# ── Login ─────────────────────────────────


class TestLogin:
    def test_login_success(self, client):
        u = _unique_user()
        client.post("/api/auth/register", json={"username": u, "password": "Pass1234!"})
        resp = client.post(
            "/api/auth/login", json={"username": u, "password": "Pass1234!"}
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == u

    def test_login_wrong_password(self, client):
        u = _unique_user()
        client.post("/api/auth/register", json={"username": u, "password": "Pass1234!"})
        resp = client.post(
            "/api/auth/login", json={"username": u, "password": "WrongPass"}
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post(
            "/api/auth/login", json={"username": "nouser999", "password": "Pass1234!"}
        )
        assert resp.status_code == 401

    def test_login_missing_body(self, client):
        resp = client.post("/api/auth/login", content_type="application/json")
        assert resp.status_code == 400


# ── Refresh ───────────────────────────────


class TestRefresh:
    def test_refresh_success(self, client, auth_tokens):
        resp = client.post(
            "/api/auth/refresh",
            headers=auth_header(auth_tokens["refresh"]),
        )
        assert resp.status_code == 200
        assert "access_token" in resp.get_json()

    def test_refresh_with_access_token_fails(self, client, auth_tokens):
        resp = client.post(
            "/api/auth/refresh",
            headers=auth_header(auth_tokens["access"]),
        )
        assert resp.status_code == 422  # flask-jwt-extended: wrong token type


# ── Logout ────────────────────────────────


class TestLogout:
    def test_logout_revokes_token(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        # 登出
        resp = client.post("/api/auth/logout", headers=hdr)
        assert resp.status_code == 200

        # 登出後再存取 /me 應被拒絕 (revoked)
        resp2 = client.get("/api/auth/me", headers=hdr)
        assert resp2.status_code == 401


# ── Me ────────────────────────────────────


class TestMe:
    def test_me_returns_user(self, client, auth_tokens):
        resp = client.get("/api/auth/me", headers=auth_header(auth_tokens["access"]))
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["user"]["username"] == auth_tokens["user"]["username"]

    def test_me_without_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401
