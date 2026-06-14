"""
admin 端點認證測試
"""

import uuid
import pytest
from models import db
from models.user import User


def _create_user(app, is_admin=False):
    """建立使用者並回傳 username"""
    username = f"adm_{uuid.uuid4().hex[:8]}"
    with app.app_context():
        u = User(username=username, display_name=username)
        u.set_password("TestPass123")
        u.is_admin = is_admin
        db.session.add(u)
        db.session.commit()
    return username


def _login(client, username):
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": "TestPass123"},
    )
    return resp.json["access_token"]


def _cleanup(app, username):
    with app.app_context():
        User.query.filter_by(username=username).delete()
        db.session.commit()


class TestAdminAuth:
    """管理員端點認證測試"""

    def test_dashboard_no_auth(self, client):
        """未認證應回 401"""
        resp = client.get("/admin/api/dashboard")
        assert resp.status_code == 401

    def test_dashboard_non_admin(self, client, app):
        """非管理員應回 403"""
        username = _create_user(app, is_admin=False)
        token = _login(client, username)
        resp = client.get(
            "/admin/api/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        assert resp.json["error"] == "需要管理員權限"
        _cleanup(app, username)

    def test_dashboard_admin_ok(self, client, app):
        """管理員應回 200"""
        username = _create_user(app, is_admin=True)
        token = _login(client, username)
        resp = client.get(
            "/admin/api/dashboard",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json["success"] is True
        _cleanup(app, username)

    def test_metrics_no_auth(self, client):
        """metrics 未認證應回 401"""
        resp = client.get("/admin/api/metrics")
        assert resp.status_code == 401

    def test_metrics_non_admin(self, client, app):
        """metrics 非管理員應回 403"""
        username = _create_user(app, is_admin=False)
        token = _login(client, username)
        resp = client.get(
            "/admin/api/metrics",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        _cleanup(app, username)

    def test_metrics_admin_ok(self, client, app):
        """metrics 管理員應回 200"""
        username = _create_user(app, is_admin=True)
        token = _login(client, username)
        resp = client.get(
            "/admin/api/metrics?hours=1",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json
        assert data["success"] is True
        assert "summary" in data
        assert "endpoints" in data
        assert "hourly_trend" in data
        _cleanup(app, username)
