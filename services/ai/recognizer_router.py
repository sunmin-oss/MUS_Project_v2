"""
辨識器路由

封裝多層 Vision Recognizer，依設定順序嘗試：
    primary  → secondary → fallback

primary/secondary 通常是同品牌（例如兩把 Gemini key），fallback 為跨品牌備援
（例如 OpenAI）。依錯誤分類決定是否切換下一層；連續失敗到達門檻會開啟熔斷，
冷卻期內直接走最末層 fallback。
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Callable, List, Optional, Tuple

from services.ai.errors import classify_exception
from services.ai import usage_log

logger = logging.getLogger(__name__)


def _provider_brand(target: Any) -> Optional[str]:
    """從辨識器類別名稱推斷品牌（gemini/google/claude/openai）。"""
    if target is None:
        return None
    name = type(target).__name__.lower()
    return next((b for b in ("gemini", "google", "claude", "openai") if b in name), None)


def _provider_model(target: Any) -> Optional[str]:
    """從 target 抽出 model 名稱（model_name / model 兩種命名都支援）。"""
    if target is None:
        return None
    for attr in ("model_name", "model"):
        v = getattr(target, attr, None)
        if isinstance(v, str) and v:
            return v
    return None


class RecognizerRouter:
    """多層 Vision Recognizer 統一介面。"""

    def __init__(
        self,
        primary: Any,
        fallback: Any = None,
        settings: Any = None,
        secondary: Any = None,
    ):
        self.primary = primary
        self.secondary = secondary
        self.fallback = fallback
        self.settings = settings

        self._lock = threading.Lock()
        self._fail_count = 0
        self._breaker_open_until = 0.0
        self.last_provider: Optional[str] = None

        # 依優先順序組裝 chain
        chain: List[Tuple[str, Any, Optional[str]]] = []
        if primary is not None:
            chain.append(("primary", primary, _provider_brand(primary)))
        if secondary is not None:
            chain.append(("secondary", secondary, _provider_brand(secondary)))
        if fallback is not None and bool(
            getattr(settings, "AI_FALLBACK_ENABLED", True)
        ):
            chain.append(
                ("openai_fallback", fallback, _provider_brand(fallback) or "openai")
            )
        self._chain = chain

    # ---------- breaker ----------

    def _is_breaker_open(self) -> bool:
        return time.time() < self._breaker_open_until

    def _open_breaker(self) -> None:
        cd = int(getattr(self.settings, "AI_FALLBACK_COOLDOWN_SEC", 300))
        self._breaker_open_until = time.time() + cd
        logger.warning("⚠ 主辨識器熔斷開啟，%ss 內走最末層 fallback", cd)

    def _record_success(self, slot_name: str) -> None:
        # 只有最前段（primary/secondary）成功才完全重置；fallback 成功不撤銷熔斷
        with self._lock:
            if slot_name in ("primary", "secondary"):
                self._fail_count = 0
                self._breaker_open_until = 0.0

    def _record_failure(self, slot_name: str) -> None:
        with self._lock:
            if slot_name in ("primary", "secondary"):
                self._fail_count += 1
                threshold = int(
                    getattr(self.settings, "AI_FALLBACK_FAIL_THRESHOLD", 3)
                )
                if self._fail_count >= threshold:
                    self._open_breaker()

    # ---------- helpers ----------

    @staticmethod
    def _has_method(target: Any, method: str) -> bool:
        return target is not None and callable(getattr(target, method, None))

    def _candidates(self, method: str) -> List[Tuple[str, Any, Optional[str]]]:
        """回傳支援該 method 的 chain 子集；熔斷時跳過前段。"""
        supported = [s for s in self._chain if self._has_method(s[1], method)]
        if self._is_breaker_open() and len(supported) > 1:
            return supported[-1:]
        return supported

    def _invoke(
        self,
        target: Any,
        name: str,
        brand: Optional[str],
        method: str,
        *args,
        **kwargs,
    ):
        max_retry = max(0, int(getattr(self.settings, "AI_MAX_RETRY", 1)))
        last_exc: Optional[BaseException] = None
        fallback_used = name != "primary"
        model = _provider_model(target)

        for attempt in range(max_retry + 1):
            t0 = time.time()
            try:
                fn: Callable = getattr(target, method)
                result = fn(*args, **kwargs)
                latency = (time.time() - t0) * 1000
                self.last_provider = name
                logger.info(
                    "✓ AI provider=%s brand=%s method=%s latency=%.1fms",
                    name, brand, method, latency,
                )
                usage_log.log_event(
                    feature=method,
                    provider=name,
                    provider_name=brand,
                    model=model,
                    success=True,
                    fallback_used=fallback_used,
                    latency_ms=latency,
                )
                return result
            except Exception as e:  # noqa: BLE001
                last_exc = e
                kind = classify_exception(e)
                latency = (time.time() - t0) * 1000
                usage_log.log_event(
                    feature=method,
                    provider=name,
                    provider_name=brand,
                    model=model,
                    success=False,
                    fallback_used=fallback_used,
                    latency_ms=latency,
                    error_type=kind,
                )
                if kind == "permanent" or attempt >= max_retry:
                    raise
                logger.info(
                    "… provider=%s method=%s 重試 %d/%d (%s): %s",
                    name, method, attempt + 1, max_retry, kind, e,
                )
        if last_exc:
            raise last_exc

    def _call(self, method: str, *args, **kwargs):
        candidates = self._candidates(method)
        if not candidates:
            raise AttributeError(f"沒有 provider 提供方法: {method}")

        for idx, (name, target, brand) in enumerate(candidates):
            try:
                result = self._invoke(target, name, brand, method, *args, **kwargs)
                self._record_success(name)
                return result
            except Exception as e:  # noqa: BLE001
                kind = classify_exception(e)
                logger.warning(
                    "⚠ provider=%s 失敗 (%s) method=%s: %s", name, kind, method, e
                )
                self._record_failure(name)
                if kind == "permanent" or idx == len(candidates) - 1:
                    raise

        raise RuntimeError("RecognizerRouter: 未預期的執行路徑")

    # ---------- 公開介面 ----------

    def recognize(self, *args, **kwargs):
        return self._call("recognize", *args, **kwargs)

    def recognize_prescription(self, *args, **kwargs):
        return self._call("recognize_prescription", *args, **kwargs)

    def search_by_text(self, *args, **kwargs):
        return self._call("search_by_text", *args, **kwargs)

    def recognize_with_rag(self, image_path, drug_db, *args, **kwargs):
        """
        RAG 辨識：在 chain 中支援 RAG 的層之間切換；
        全部失敗或都不支援 RAG，再退化為普通 recognize。
        """
        rag_candidates = self._candidates("recognize_with_rag")
        for idx, (name, target, brand) in enumerate(rag_candidates):
            try:
                result = self._invoke(
                    target, name, brand, "recognize_with_rag",
                    image_path, drug_db, *args, **kwargs,
                )
                self._record_success(name)
                return result
            except Exception as e:  # noqa: BLE001
                kind = classify_exception(e)
                logger.warning("⚠ provider=%s RAG 失敗 (%s)：%s", name, kind, e)
                self._record_failure(name)
                if kind == "permanent":
                    raise
                if idx < len(rag_candidates) - 1:
                    continue
                logger.info("… RAG 全部失敗，退化為普通 recognize")
                break

        if any(self._has_method(t, "recognize") for _, t, _ in self._chain):
            return self._call("recognize", image_path)
        raise RuntimeError("沒有可用的辨識器")

    # ---------- 透傳其他屬性 ----------

    def __getattr__(self, name: str):
        primary = object.__getattribute__(self, "primary")
        if primary is not None and hasattr(primary, name):
            return getattr(primary, name)
        raise AttributeError(name)
