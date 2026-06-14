"""Auth + User Model 測試（A1-1 / A1-2 DoD）"""

import pytest
from models import db
from models.user import User


def test_user_table_created(app):
    """users 表由 create_all 自動建立"""
    with app.app_context():
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        assert "users" in tables


def test_register_success(client):
    """正常註冊回傳 201"""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "testuser1",
            "password": "Test1234!",
            "display_name": "測試使用者",
        },
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert "user_id" in data

    # 清理
    with client.application.app_context():
        User.query.filter_by(username="testuser1").delete()
        db.session.commit()


def test_register_duplicate_username(client):
    """重複使用者名稱回傳 409"""
    payload = {"username": "dupuser", "password": "Test1234!"}
    resp1 = client.post("/api/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = client.post("/api/auth/register", json=payload)
    assert resp2.status_code == 409

    # 清理
    with client.application.app_context():
        User.query.filter_by(username="dupuser").delete()
        db.session.commit()


def test_register_short_username(client):
    """使用者名稱太短回傳 400"""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "ab",
            "password": "Test1234!",
        },
    )
    assert resp.status_code == 400


def test_register_short_password(client):
    """密碼太短回傳 400"""
    resp = client.post(
        "/api/auth/register",
        json={
            "username": "validuser",
            "password": "short",
        },
    )
    assert resp.status_code == 400


def test_register_missing_body(client):
    """缺少 JSON body 回傳 400"""
    resp = client.post("/api/auth/register", content_type="application/json")
    assert resp.status_code == 400


def test_password_hash_not_plain(client):
    """密碼應被 bcrypt 雜湊而非明文存放"""
    client.post(
        "/api/auth/register",
        json={
            "username": "hashtest",
            "password": "Test1234!",
        },
    )
    with client.application.app_context():
        user = User.query.filter_by(username="hashtest").first()
        assert user is not None
        assert user.password_hash != "Test1234!"
        assert user.check_password("Test1234!") is True
        assert user.check_password("wrong") is False

        User.query.filter_by(username="hashtest").delete()
        db.session.commit()
