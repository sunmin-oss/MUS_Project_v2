"""pytest 共用 fixtures（P0-4 + Sprint 2）"""

import os
import sys

import pytest

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def app():
    """提供測試用 Flask app（使用既有 drug_recognition.db）"""
    from main import app as flask_app

    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture
def client(app):
    """提供 Flask test client"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """提供 SQLAlchemy session（在 app context 內）"""
    from models import db

    with app.app_context():
        yield db.session


@pytest.fixture
def auth_tokens(client, app):
    """註冊 + 登入並回傳 access / refresh token"""
    import uuid

    username = f"test_{uuid.uuid4().hex[:8]}"
    client.post("/api/auth/register", json={
        "username": username,
        "password": "Test1234!",
        "display_name": "測試使用者",
    })
    resp = client.post("/api/auth/login", json={
        "username": username,
        "password": "Test1234!",
    })
    data = resp.get_json()
    return {
        "access": data["access_token"],
        "refresh": data["refresh_token"],
        "user": data["user"],
    }


def auth_header(token):
    """產生 Authorization header"""
    return {"Authorization": f"Bearer {token}"}
