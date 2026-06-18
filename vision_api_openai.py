"""
OpenAI Vision Recognizer (Phase 1)

提供 recognize() 與 recognize_prescription() 兩個介面，
作為 Gemini/Google 主辨識器的備援，被 services.ai.RecognizerRouter 自動切換。

僅依賴 requests，不引入 openai SDK。
"""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from services.ai.errors import ProviderError

logger = logging.getLogger(__name__)


_RECOGNIZE_PROMPT = (
    "請分析這張圖片中的藥物，並輸出 JSON：\n"
    "{\n"
    '  "has_medicine": true 或 false,\n'
    '  "medicines": [\n'
    "    {\n"
    '      "name": "藥物名稱（盡量為繁體中文，否則保留英文）",\n'
    '      "shape": "形狀",\n'
    '      "color": "顏色",\n'
    '      "markings": "刻字或標記，沒有則填 \\"\\"",\n'
    '      "confidence": 0~1 的浮點數,\n'
    '      "description": "簡短描述"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "規則：\n"
    "1. 只回傳 JSON，不要任何解說文字。\n"
    "2. 若無法確定為藥物，has_medicine=false 且 medicines=[]。\n"
    "3. 最多列出 5 種。"
)


_PRESCRIPTION_PROMPT = (
    "請從這張藥單影像辨識所有藥物名稱，輸出 JSON：\n"
    '{"drugs": ["藥名1", "藥名2", ...]}\n'
    "規則：\n"
    "1. 只回傳 JSON，不要任何解說文字。\n"
    "2. 名稱優先使用單據上的標示原文，不要自行翻譯成其他語言。\n"
    "3. 若辨識不到藥名，drugs 為空陣列。"
)


class OpenAIVisionRecognizer:
    """以 OpenAI Chat Completions（multimodal）做藥物辨識的最小可用實作。"""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 20,
        max_tokens: int = 600,
    ):
        if not api_key:
            raise ValueError("OpenAI API Key 未提供")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_tokens = max_tokens

    # ---------- public ----------

    def recognize(self, image_path: str) -> List[Dict[str, Any]]:
        data = self._chat_image(image_path, _RECOGNIZE_PROMPT, expect_json=True)
        if not isinstance(data, dict):
            return []
        if not data.get("has_medicine"):
            return []
        results: List[Dict[str, Any]] = []
        for m in (data.get("medicines") or [])[:10]:
            if not isinstance(m, dict):
                continue
            try:
                conf = float(m.get("confidence", 0.5) or 0.5)
            except (TypeError, ValueError):
                conf = 0.5
            results.append(
                {
                    "name": str(m.get("name") or "未知藥物").strip(),
                    "confidence": max(0.0, min(1.0, conf)),
                    "description": str(m.get("description") or ""),
                    "shape": str(m.get("shape") or ""),
                    "color": str(m.get("color") or ""),
                    "markings": str(m.get("markings") or ""),
                    "source": "openai_vision",
                }
            )
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    def recognize_prescription(self, image_path: str) -> List[str]:
        data = self._chat_image(image_path, _PRESCRIPTION_PROMPT, expect_json=True)
        if not isinstance(data, dict):
            return []
        names = data.get("drugs") or []
        return [str(n).strip() for n in names if isinstance(n, str) and n.strip()][:20]

    # ---------- internal ----------

    def _chat_image(
        self, image_path: str, prompt: str, expect_json: bool = True
    ) -> Optional[Dict[str, Any]]:
        image_part = self._build_image_part(image_path)

        messages = [
            {"role": "system", "content": "你是專業的藥物辨識助手，只回傳合法 JSON。"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    image_part,
                ],
            },
        ]
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.1,
        }
        if expect_json:
            payload["response_format"] = {"type": "json_object"}

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                url, headers=headers, json=payload, timeout=self.timeout
            )
        except requests.exceptions.Timeout as e:
            raise ProviderError("OpenAI Vision 逾時", kind="retryable", original=e) from e
        except requests.exceptions.ConnectionError as e:
            raise ProviderError(
                "OpenAI Vision 連線失敗", kind="retryable", original=e
            ) from e

        if resp.status_code != 200:
            body = resp.text[:300]
            kind = "retryable"
            if resp.status_code == 429 or "insufficient_quota" in body.lower():
                kind = "quota"
            elif 400 <= resp.status_code < 500 and resp.status_code != 408:
                kind = "permanent"
            raise ProviderError(
                f"OpenAI Vision 錯誤 {resp.status_code}: {body}",
                kind=kind,
                status_code=resp.status_code,
            )

        try:
            content = resp.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(
                "OpenAI Vision 回應格式異常", kind="retryable", original=e
            ) from e

        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            logger.warning("OpenAI Vision 回傳非 JSON：%s", str(content)[:200])
            return None

    @staticmethod
    def _build_image_part(image_path: str) -> Dict[str, Any]:
        ext = Path(image_path).suffix.lower().lstrip(".") or "jpeg"
        if ext == "jpg":
            ext = "jpeg"
        if ext not in ("png", "jpeg", "gif", "webp", "bmp"):
            ext = "jpeg"
        with open(image_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("ascii")
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/{ext};base64,{b64}"},
        }
