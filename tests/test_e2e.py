"""Sprint 4 — E2E 全鏈路測試"""

import uuid
import pytest
from tests.conftest import auth_header


class TestE2EMedicationFlow:
    """E2E: 註冊 → 建 profile → 新增用藥 → 排程 → 服藥 → 統計"""

    def test_full_medication_lifecycle(self, client, app):
        username = f"e2e_{uuid.uuid4().hex[:8]}"

        # 1. 註冊
        r = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": "Test1234!",
            },
        )
        assert r.status_code == 201

        # 2. 登入
        r = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": "Test1234!",
            },
        )
        assert r.status_code == 200
        token = r.get_json()["access_token"]
        hdr = auth_header(token)

        # 3. 建 profile
        r = client.post(
            "/api/auth/profiles",
            headers=hdr,
            json={
                "name": "本人",
                "relationship": "本人",
            },
        )
        assert r.status_code == 201
        pid = r.get_json()["profile"]["id"]

        # 4. 新增用藥 + 排程
        r = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "普拿疼",
                "profile_id": pid,
                "dosage": "1",
                "unit": "顆",
                "frequency": "tid",
                "start_date": "2026-05-27",
                "stock_qty": 20,
                "schedules": [
                    {"time_slot": "morning", "scheduled_time": "08:00"},
                    {"time_slot": "noon", "scheduled_time": "12:00"},
                    {"time_slot": "evening", "scheduled_time": "18:00"},
                ],
            },
        )
        assert r.status_code == 201
        med = r.get_json()["medication"]
        mid = med["id"]
        assert len(med["schedules"]) == 3

        # 5. 記錄服藥
        r = client.post(
            "/api/user/adherence",
            headers=hdr,
            json={
                "medication_id": mid,
                "status": "taken",
                "scheduled_date": "2026-05-27",
            },
        )
        assert r.status_code == 201

        # 6. 查詢用藥（庫存應扣減）
        r = client.get(f"/api/user/medications/{mid}", headers=hdr)
        assert r.get_json()["medication"]["stock_qty"] == 19

        # 7. 服藥統計
        r = client.get("/api/user/adherence/stats?days=30", headers=hdr)
        stats = r.get_json()["stats"]
        assert stats["taken"] >= 1
        assert stats["adherence_rate"] > 0

        # 8. 查看服藥紀錄
        r = client.get(
            "/api/user/adherence?start=2026-05-01&end=2026-05-31", headers=hdr
        )
        assert len(r.get_json()["logs"]) >= 1

        # 9. 停用用藥
        r = client.put(
            f"/api/user/medications/{mid}",
            headers=hdr,
            json={
                "is_active": False,
            },
        )
        assert r.status_code == 200
        assert r.get_json()["medication"]["is_active"] is False


class TestE2ESafetyFlow:
    """E2E: 註冊 → 設定過敏 → 安全檢查"""

    def test_full_safety_check_flow(self, client, app):
        username = f"e2e_safe_{uuid.uuid4().hex[:8]}"

        # 1. 註冊 + 登入
        client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": "Test1234!",
            },
        )
        r = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": "Test1234!",
            },
        )
        token = r.get_json()["access_token"]
        hdr = auth_header(token)

        # 2. 建立成分（直接用 ORM）
        from models import db
        from models.safety import Ingredient

        with app.app_context():
            ing = Ingredient(name=f"E2E成分_{uuid.uuid4().hex[:6]}")
            db.session.add(ing)
            db.session.commit()
            ing_id = ing.id

        # 3. 設定過敏
        r = client.post(
            "/api/safety/allergies",
            headers=hdr,
            json={
                "ingredient_id": ing_id,
                "severity": "severe",
            },
        )
        assert r.status_code == 201

        # 4. 查看過敏清單
        r = client.get("/api/safety/allergies", headers=hdr)
        assert len(r.get_json()["allergies"]) >= 1

        # 5. 對任意藥物做安全檢查（drug_id=1）
        r = client.post("/api/safety/check", headers=hdr, json={"drug_id": 1})
        assert r.status_code == 200
        data = r.get_json()
        assert data["overall"] in ("safe", "warning", "danger")
        assert len(data["checks"]) == 3  # allergy + duplicate + interaction

        # 6. 查詢交互作用列表
        r = client.get("/api/safety/interactions", headers=hdr)
        assert r.status_code == 200
        assert "interactions" in r.get_json()

        # 7. 刪除過敏
        allergies = client.get("/api/safety/allergies", headers=hdr).get_json()[
            "allergies"
        ]
        for a in allergies:
            if a["ingredient_id"] == ing_id:
                r = client.delete(f"/api/safety/allergies/{a['id']}", headers=hdr)
                assert r.status_code == 200


class TestE2EPushTokenFlow:
    """E2E: 註冊 → Push Token → 推播"""

    def test_push_token_lifecycle(self, client, app):
        username = f"e2e_push_{uuid.uuid4().hex[:8]}"

        # 1. 註冊 + 登入
        client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": "Test1234!",
            },
        )
        r = client.post(
            "/api/auth/login",
            json={
                "username": username,
                "password": "Test1234!",
            },
        )
        token = r.get_json()["access_token"]
        hdr = auth_header(token)
        uid = r.get_json()["user"]["id"]

        # 2. 註冊 push token
        device_token = f"apns-{uuid.uuid4().hex}"
        r = client.post(
            "/api/user/push-token",
            headers=hdr,
            json={
                "token": device_token,
                "platform": "ios",
            },
        )
        assert r.status_code == 200

        # 3. 用推播服務發送
        from services.push_service import push_service

        with app.app_context():
            result = push_service.send_to_user(uid, "測試", "推播內容")
            assert result is True

        # 4. 取消 token
        r = client.delete(
            "/api/user/push-token",
            headers=hdr,
            json={
                "token": device_token,
            },
        )
        assert r.status_code == 200
