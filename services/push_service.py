"""
推播通知服務（S1-5 Mock 版）

現階段不使用真實 APNs，僅記錄推播 log 供開發測試。
Sprint 5+ 正式環境再接入 APNs / FCM。
"""

import logging
from datetime import datetime
from typing import Optional

from models import db
from models.medication import PushToken

logger = logging.getLogger(__name__)


class PushNotification:
    """一則推播通知"""

    def __init__(
        self, user_id: int, title: str, body: str, data: Optional[dict] = None
    ):
        self.user_id = user_id
        self.title = title
        self.body = body
        self.data = data or {}
        self.sent_at = None
        self.status = "pending"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "title": self.title,
            "body": self.body,
            "data": self.data,
            "status": self.status,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


class PushService:
    """
    Mock 推播服務。

    - 記錄所有推播到 _log（in-memory）
    - 提供 send() 介面，日後替換為 APNs / FCM 真實發送
    """

    def __init__(self):
        self._log: list[dict] = []

    @property
    def log(self) -> list[dict]:
        return self._log[-100:]  # 最近 100 筆

    def send(self, notification: PushNotification) -> bool:
        """
        發送推播（mock：僅寫入 log）。

        回傳 True 代表成功。
        """
        # 查詢使用者的 active push tokens
        tokens = PushToken.query.filter_by(
            user_id=notification.user_id, is_active=True
        ).all()

        if not tokens:
            notification.status = "no_token"
            self._log.append(notification.to_dict())
            logger.info(
                f"📱 [MOCK] 推播跳過（無 token）: user={notification.user_id} "
                f"title={notification.title}"
            )
            return False

        # Mock: 假裝發送成功
        notification.status = "sent"
        notification.sent_at = datetime.utcnow()

        for token in tokens:
            entry = notification.to_dict()
            entry["token_platform"] = token.platform
            self._log.append(entry)

        logger.info(
            f"📱 [MOCK] 推播已發送: user={notification.user_id} "
            f"title={notification.title} tokens={len(tokens)}"
        )
        return True

    def send_to_user(
        self, user_id: int, title: str, body: str, data: Optional[dict] = None
    ) -> bool:
        """便捷方法"""
        return self.send(
            PushNotification(user_id=user_id, title=title, body=body, data=data)
        )


# 全域 singleton
push_service = PushService()
