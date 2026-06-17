"""
辨識器路由 (Phase 1)

封裝主辨識器（Gemini/Google/Claude）與 OpenAI 備援辨識器，
依錯誤分類決定是否切換 fallback，並提供熔斷冷卻避免反覆失敗。
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, Optional

from services.ai.errors import classify_exception

logger = logging.getLogger(__name__)


class RecognizerRouter:
    """主 / 備援 Vision Recognizer 統一介面。"""

    def __init__(self, primary: Any, fallback: Any, settings: Any):
        self.primary = primary
        self.fallback = fallback
        self.settings = settings

        self._lock = threading.Lock()
        self._fail_count = 0
        self._breaker_open_until = 0.0
        # 上一次成功使用的 provider（"primary" / "openai_fallback"），供回應標示
        self.last_provider: Optional[str] = None

    # ---------- breaker ----------

    @property
    def fallback_enabled(self) -> bool:
        return bool(self.fallback) and bool(
            getattr(self.settings, "AI_FALLBACK_ENABLED", True)
        )

    def _is_breaker_open(self) -> bool:
        return time.time() < self._breaker_open_until

    def _open_breaker(self) -> None:
        cd = int(getattr(self.settings, "AI_FALLBACK_COOLDOWN_SEC", 300))
        self._breaker_open_until = time.time() + cd
        logger.warning("⚠ 主辨識器熔斷開啟，%ss 內走 fallback", cd)

    def _record_success(self) -> None:
        with self._lock:
            self._fail_count = 0
            self._breaker_open_until = 0.0

    def _record_failure(self) -> None:
        with self._lock:
            self._fail_count += 1
            threshold = int(getattr(self.settings, "AI_FALLBACK_FAIL_THRESHOLD", 3))
            if self._fail_count >= threshold:
                self._open_breaker()

    # ---------- helpers ----------

    @staticmethod
    def _has_method(target: Any, method: str) -> bool:
        return target is not None and callable(getattr(target, method, None))

    def _invoke(self, target: Any, name: str, method: str, *args, **kwargs):
        max_retry = max(0, int(getattr(self.settings, "AI_MAX_RETRY", 1)))
        last_exc: Optional[BaseException] = None
        for attempt in range(max_retry + 1):
            t0 = time.time()
            try:
                fn: Callable = getattr(target, method)
                result = fn(*args, **kwargs)
                latency = (time.time() - t0) * 1000
                self.last_provider = name
                logger.info(
                    "✓ AI provider=%s method=%s latency=%.1fms", name, method, latency
                )
                return result
            except Exception as e:  # noqa: BLE001
                last_exc = e
                kind = classify_exception(e)
                if kind == "permanent" or attempt >= max_retry:
                    raise
                logger.info(
                    "… provider=%s method=%s 重試 %d/%d (%s): %s",
                    name,
                    method,
                    attempt + 1,
                    max_retry,
                    kind,
                    e,
                )
        # 理論上不會到這
        if last_exc:
            raise last_exc

    def _call(self, method: str, *args, **kwargs):
        primary_supported = self._has_method(self.primary, method)
        fallback_supported = self._has_method(self.fallback, method)

        # 主不支援 → 直接 fallback
        if not primary_supported:
            if fallback_supported and self.fallback_enabled:
                return self._invoke(
                    self.fallback, "openai_fallback", method, *args, **kwargs
                )
            raise AttributeError(f"沒有 provider 提供方法: {method}")

        # 熔斷開啟 → 先試 fallback，失敗再試主（半開）
        if self._is_breaker_open() and fallback_supported and self.fallback_enabled:
            try:
                return self._invoke(
                    self.fallback, "openai_fallback", method, *args, **kwargs
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("⚠ 熔斷期間 fallback 也失敗，回退主路徑試一次: %s", e)

        # 嘗試主
        try:
            result = self._invoke(self.primary, "primary", method, *args, **kwargs)
            self._record_success()
            return result
        except Exception as e:  # noqa: BLE001
            kind = classify_exception(e)
            logger.warning("⚠ 主辨識器失敗 (%s) method=%s: %s", kind, method, e)
            if kind == "permanent" or not self.fallback_enabled or not fallback_supported:
                raise
            self._record_failure()
            return self._invoke(
                self.fallback, "openai_fallback", method, *args, **kwargs
            )

    # ---------- 公開介面（與既有 recognizer 同名）----------

    def recognize(self, *args, **kwargs):
        return self._call("recognize", *args, **kwargs)

    def recognize_prescription(self, *args, **kwargs):
        return self._call("recognize_prescription", *args, **kwargs)

    def search_by_text(self, *args, **kwargs):
        return self._call("search_by_text", *args, **kwargs)

    def recognize_with_rag(self, image_path, drug_db, *args, **kwargs):
        """
        RAG 辨識特殊處理：fallback 端通常沒有 RAG，
        若主辨識器拋暫時性錯誤，自動退化為呼叫 fallback.recognize。
        """
        if self._has_method(self.primary, "recognize_with_rag") and not self._is_breaker_open():
            try:
                result = self._invoke(
                    self.primary,
                    "primary",
                    "recognize_with_rag",
                    image_path,
                    drug_db,
                    *args,
                    **kwargs,
                )
                self._record_success()
                return result
            except Exception as e:  # noqa: BLE001
                kind = classify_exception(e)
                logger.warning("⚠ 主 RAG 失敗 (%s)：%s", kind, e)
                if kind == "permanent":
                    raise
                self._record_failure()

        # 退化為普通辨識（無 RAG）
        if self._has_method(self.fallback, "recognize") and self.fallback_enabled:
            return self._invoke(
                self.fallback, "openai_fallback", "recognize", image_path
            )
        if self._has_method(self.primary, "recognize"):
            return self._invoke(self.primary, "primary", "recognize", image_path)
        raise RuntimeError("沒有可用的辨識器")

    # ---------- 透傳其他屬性（如 search_by_drug_id 等） ----------

    def __getattr__(self, name: str):
        # 只有當上面顯式定義都找不到才會走到這
        primary = object.__getattribute__(self, "primary")
        if primary is not None and hasattr(primary, name):
            return getattr(primary, name)
        raise AttributeError(name)
