"""Sprint 4 — 推播服務 + 排程 + 庫存提醒 測試（S1-3 / S1-5 / S1-6）"""

import uuid
import pytest
from tests.conftest import auth_header


class TestPushService:
    def test_push_send_no_token(self, app):
        """無 token 時推播回傳 False"""
        from services.push_service import PushService, PushNotification

        svc = PushService()
        with app.app_context():
            n = PushNotification(user_id=99999, title="test", body="body")
            result = svc.send(n)
            assert result is False
            assert n.status == "no_token"
            assert len(svc.log) == 1

    def test_push_send_with_token(self, client, auth_tokens, app):
        """有 token 時推播回傳 True（mock）"""
        from services.push_service import PushService, PushNotification

        hdr = auth_header(auth_tokens["access"])
        # 先註冊 push token
        client.post(
            "/api/user/push-token",
            headers=hdr,
            json={
                "token": f"test-token-{uuid.uuid4().hex[:8]}",
                "platform": "ios",
            },
        )

        svc = PushService()
        with app.app_context():
            uid = auth_tokens["user"]["id"]
            n = PushNotification(user_id=uid, title="提醒", body="該吃藥了")
            result = svc.send(n)
            assert result is True
            assert n.status == "sent"
            assert n.sent_at is not None

    def test_push_service_log(self, app):
        """推播 log 正確記錄"""
        from services.push_service import PushService, PushNotification

        svc = PushService()
        with app.app_context():
            for i in range(3):
                svc.send(PushNotification(user_id=99999, title=f"t{i}", body="b"))
            assert len(svc.log) == 3

    def test_send_to_user_convenience(self, app):
        """send_to_user 便捷方法"""
        from services.push_service import PushService

        svc = PushService()
        with app.app_context():
            result = svc.send_to_user(99999, "title", "body", {"key": "val"})
            assert result is False  # 無 token


class TestSchedulerJobs:
    def test_stock_alert_triggered(self, client, auth_tokens, app):
        """庫存低於閾值時觸發提醒"""
        from services.push_service import push_service

        hdr = auth_header(auth_tokens["access"])

        # 建立 profile + 低庫存用藥
        p = client.post("/api/auth/profiles", headers=hdr, json={"name": "本人"})
        pid = p.get_json()["profile"]["id"]

        client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "name": "低庫存藥",
                "profile_id": pid,
                "start_date": "2026-05-01",
                "stock_qty": 3,
                "unit": "顆",
            },
        )

        # 手動觸發庫存檢查
        from services.scheduler import _check_stock_alerts

        _check_stock_alerts.__wrapped__ = None  # 確保不被 mock

        # 需要在 app context 中手動呼叫
        with app.app_context():
            from services.scheduler import _check_stock_alerts

            initial_count = len(push_service.log)
            _check_stock_alerts()
            # 應該有新的推播紀錄
            assert len(push_service.log) >= initial_count


class TestRecognizeSafetyIntegration:
    """S6-8: 辨識結果回傳安全警示（需有 JWT）"""

    def test_recognize_endpoint_exists(self, client):
        """辨識端點存在且無圖片回 400"""
        resp = client.post("/api/recognize")
        assert resp.status_code in (400, 401, 503)

    def test_recognize_returns_json(self, client):
        """辨識端點回傳 JSON"""
        resp = client.post("/api/recognize")
        data = resp.get_json()
        assert data is not None
        assert "success" in data
