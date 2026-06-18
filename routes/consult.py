"""
AI 諮詢路由 (Phase 1)

POST /api/consult
    {
      "question": "...",                  # 任一個
      "messages": [{"role":"user","content":"..."}, ...]
    }

回應:
    {
      "success": true,
      "answer": "...（含風險告知）",
      "model": "gpt-4o-mini",
      "usage": {...}
    }

未設定 OPENAI_CONSULT_API_KEY 時回 503，error_type="not_configured"。
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from flask import Blueprint, jsonify, request

from config import config
from services.ai.consult_client import ConsultClient
from services.ai.errors import ProviderError

logger = logging.getLogger(__name__)

consult_bp = Blueprint("consult", __name__, url_prefix="/api")

DISCLAIMER = "\n\n⚠ 本回覆僅供參考，不構成醫療建議。請依藥師、醫師指示用藥。"

_client: ConsultClient | None = None


def _get_client() -> ConsultClient | None:
    """延遲建立 ConsultClient；無 Key B 時回 None。"""
    global _client
    if _client is not None:
        return _client
    if not getattr(config, "OPENAI_CONSULT_API_KEY", None):
        return None
    _client = ConsultClient(
        api_key=config.OPENAI_CONSULT_API_KEY,
        model=config.OPENAI_CONSULT_MODEL,
        base_url=config.OPENAI_CONSULT_BASE_URL,
        timeout=config.AI_TIMEOUT_SEC,
        max_tokens=config.AI_CONSULT_MAX_TOKENS,
    )
    logger.info(
        "✓ AI 諮詢已啟用 (model=%s, key=…%s)",
        config.OPENAI_CONSULT_MODEL,
        config.OPENAI_CONSULT_API_KEY[-4:] if config.OPENAI_CONSULT_API_KEY else "",
    )
    return _client


def _normalize_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    msgs: List[Dict[str, Any]] = []
    raw = payload.get("messages")
    if isinstance(raw, list):
        for m in raw:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role") or "").strip()
            content = m.get("content")
            if role not in ("user", "assistant"):
                continue
            if not isinstance(content, str):
                continue
            content = content.strip()
            if not content:
                continue
            msgs.append({"role": role, "content": content[:4000]})

    question = payload.get("question")
    if isinstance(question, str) and question.strip():
        msgs.append({"role": "user", "content": question.strip()[:4000]})

    # 只留最近 20 則，避免 prompt 過長
    return msgs[-20:]


@consult_bp.route("/consult", methods=["POST"])
@consult_bp.route("/consultation/ask", methods=["POST"])
def consult():
    client = _get_client()
    if client is None:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "AI 諮詢功能尚未啟用",
                    "error_type": "not_configured",
                }
            ),
            503,
        )

    payload = request.get_json(silent=True) or {}
    messages = _normalize_messages(payload)
    if not messages:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "缺少 question 或 messages",
                    "error_type": "invalid_request",
                }
            ),
            400,
        )

    try:
        result = client.chat(messages)
    except ProviderError as e:
        status = 502 if e.kind == "retryable" else (429 if e.kind == "quota" else 400)
        logger.warning("AI 諮詢失敗 kind=%s: %s", e.kind, e)
        return (
            jsonify(
                {
                    "success": False,
                    "error": str(e),
                    "error_type": e.kind,
                }
            ),
            status,
        )
    except Exception as e:  # noqa: BLE001
        logger.error("AI 諮詢未預期錯誤: %s", e, exc_info=True)
        return (
            jsonify(
                {"success": False, "error": "伺服器錯誤", "error_type": "internal"}
            ),
            500,
        )

    answer = (result.get("answer") or "").strip()
    if answer and DISCLAIMER.strip() not in answer:
        answer = answer + DISCLAIMER

    return jsonify(
        {
            "success": True,
            "answer": answer,
            "model": result.get("model"),
            "usage": result.get("usage", {}),
        }
    )
