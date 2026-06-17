"""
AI 錯誤分類

把各 provider（Gemini / Google Vision / Claude / OpenAI / requests）拋出的例外，
歸納成三類，供 router 決定是否切換備援：

- retryable：暫時性錯誤（timeout / connection / 5xx），可重試或切備援
- quota：配額/限速問題（429、insufficient_quota、RESOURCE_EXHAUSTED），切備援
- permanent：請求本身有問題（400/401/403/415、ValueError），不切備援
"""

from __future__ import annotations

from typing import Optional


class ProviderError(Exception):
    """供辨識器/客戶端主動拋出時帶分類資訊。"""

    def __init__(
        self,
        message: str,
        kind: str = "retryable",
        status_code: Optional[int] = None,
        original: Optional[BaseException] = None,
    ):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.original = original


_RETRYABLE_HTTP = {408, 500, 502, 503, 504}
_QUOTA_HTTP = {429}
_PERMANENT_HTTP = {400, 401, 403, 404, 405, 413, 415, 422}


def classify_exception(exc: BaseException) -> str:
    """根據例外型別與訊息推斷錯誤類型。

    回傳 "retryable" | "quota" | "permanent"
    """
    if isinstance(exc, ProviderError):
        return exc.kind

    # requests 層的網路問題
    try:
        import requests  # 延遲匯入避免硬依賴

        if isinstance(exc, requests.exceptions.Timeout):
            return "retryable"
        if isinstance(exc, requests.exceptions.ConnectionError):
            return "retryable"
    except Exception:
        pass

    # 文字訊息比對（涵蓋 Exception(f"... {status} ...") 的常見格式）
    msg = str(exc).lower()

    if any(k in msg for k in ("insufficient_quota", "resource_exhausted", "quota")):
        return "quota"
    if "rate limit" in msg or "rate_limit" in msg:
        return "quota"
    if " 429" in msg or "(429)" in msg or "status 429" in msg or "code 429" in msg:
        return "quota"

    for code in _RETRYABLE_HTTP:
        token = str(code)
        if (
            f" {token}" in msg
            or f"({token})" in msg
            or f"status {token}" in msg
            or f"code {token}" in msg
        ):
            return "retryable"
    if "timeout" in msg or "timed out" in msg:
        return "retryable"

    for code in _PERMANENT_HTTP:
        token = str(code)
        if (
            f" {token}" in msg
            or f"({token})" in msg
            or f"status {token}" in msg
            or f"code {token}" in msg
        ):
            return "permanent"
    if isinstance(exc, (ValueError, TypeError, KeyError)):
        return "permanent"

    return "retryable"
