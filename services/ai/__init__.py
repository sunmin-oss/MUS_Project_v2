"""
AI 服務模組

提供 Vision API 路由（含 OpenAI 備援）與 AI 諮詢用戶端。
"""

from services.ai.errors import classify_exception, ProviderError
from services.ai.recognizer_router import RecognizerRouter
from services.ai.consult_client import ConsultClient

__all__ = [
    "classify_exception",
    "ProviderError",
    "RecognizerRouter",
    "ConsultClient",
]
