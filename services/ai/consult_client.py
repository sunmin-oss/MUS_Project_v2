"""
AI 諮詢用戶端 (Phase 1)

獨立使用 OpenAI Key B，不與辨識備援共用流量；
只暴露 chat() 介面，供 routes/consult.py 包裝為 HTTP API。
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from services.ai.errors import ProviderError
from services.ai import usage_log

logger = logging.getLogger(__name__)


DEFAULT_SYSTEM_PROMPT = (
    "你是台灣『藥知道』用藥諮詢助理，僅回答藥物、用藥安全、健保藥品、副作用、"
    "交互作用等用藥常識；不提供診斷或處方，遇複雜問題請建議使用者諮詢醫師或藥師。"
    "請使用繁體中文，並避免揣測病情。"
)


class ConsultClient:
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 20,
        max_tokens: int = 800,
    ):
        if not api_key:
            raise ValueError("OpenAI Consult API Key 未提供")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_tokens = max_tokens

    def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        傳入 OpenAI chat 格式 messages（不含 system），回傳：
            {"answer": str, "model": str, "usage": dict}
        """
        sys_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT
        msgs = [{"role": "system", "content": sys_prompt}] + list(messages or [])

        payload = {
            "model": self.model,
            "messages": msgs,
            "max_tokens": int(max_tokens or self.max_tokens),
            "temperature": 0.4,
        }
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        t0 = time.time()
        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            usage_log.log_event(
                feature="consult",
                provider="openai_consult",
                provider_name=self.brand,
                model=self.model,
                success=False,
                latency_ms=(time.time() - t0) * 1000,
                error_type="retryable",
            )
            raise ProviderError("OpenAI 諮詢逾時", kind="retryable", original=e) from e
        except requests.exceptions.ConnectionError as e:
            usage_log.log_event(
                feature="consult",
                provider="openai_consult",
                provider_name=self.brand,
                model=self.model,
                success=False,
                latency_ms=(time.time() - t0) * 1000,
                error_type="retryable",
            )
            raise ProviderError(
                "OpenAI 諮詢連線失敗", kind="retryable", original=e
            ) from e

        latency = (time.time() - t0) * 1000

        if resp.status_code != 200:
            body = resp.text[:300]
            kind = "retryable"
            if resp.status_code == 429 or "insufficient_quota" in body.lower():
                kind = "quota"
            elif 400 <= resp.status_code < 500 and resp.status_code != 408:
                kind = "permanent"
            elif 500 <= resp.status_code < 600:
                kind = "retryable"
            logger.warning(
                "AI consult fail status=%s latency=%.1fms kind=%s",
                resp.status_code,
                latency,
                kind,
            )
            usage_log.log_event(
                feature="consult",
                provider="openai_consult",
                provider_name=self.brand,
                model=self.model,
                success=False,
                latency_ms=latency,
                status_code=resp.status_code,
                error_type=kind,
            )
            raise ProviderError(
                f"OpenAI 諮詢錯誤 {resp.status_code}: {body}",
                kind=kind,
                status_code=resp.status_code,
            )

        data = resp.json()
        try:
            answer = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            usage_log.log_event(
                feature="consult",
                provider="openai_consult",
                provider_name=self.brand,
                model=self.model,
                success=False,
                latency_ms=latency,
                status_code=resp.status_code,
                error_type="retryable",
            )
            raise ProviderError(
                "OpenAI 諮詢回應格式異常", kind="retryable", original=e
            ) from e

        usage = data.get("usage", {}) or {}
        logger.info(
            "AI consult ok latency=%.1fms tokens_in=%s tokens_out=%s",
            latency,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        usage_log.log_event(
            feature="consult",
            provider="openai_consult",
            provider_name=self.brand,
            model=self.model,
            success=True,
            latency_ms=latency,
            status_code=resp.status_code,
            tokens_in=int(usage.get("prompt_tokens") or 0) or None,
            tokens_out=int(usage.get("completion_tokens") or 0) or None,
        )
        return {"answer": answer, "model": self.model, "usage": usage}
