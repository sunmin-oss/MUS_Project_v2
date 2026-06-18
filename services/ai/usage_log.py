"""
AI Provider 使用紀錄 (Phase 2)

每次呼叫主辨識器、OpenAI 備援辨識器、AI 諮詢都會寫入 ai_provider_logs。
採背景批次寫入，避免影響請求延遲。
"""

from __future__ import annotations

import logging
import queue as _queue
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import config

logger = logging.getLogger(__name__)


_LOG_FLUSH_INTERVAL = 2  # 秒
_LOG_BATCH_SIZE = 50

_ai_log_queue: "_queue.Queue[tuple]" = _queue.Queue(maxsize=2000)
_writer_started = False
_writer_lock = threading.Lock()


def ensure_table() -> None:
    """建立 ai_provider_logs 表（若不存在）。"""
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_provider_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature TEXT NOT NULL,
                provider TEXT NOT NULL,
                provider_name TEXT,
                model TEXT,
                success INTEGER NOT NULL,
                fallback_used INTEGER NOT NULL DEFAULT 0,
                latency_ms REAL,
                status_code INTEGER,
                error_type TEXT,
                tokens_in INTEGER,
                tokens_out INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # 舊表 migration：補上 model 欄位
        try:
            conn.execute("ALTER TABLE ai_provider_logs ADD COLUMN model TEXT")
        except sqlite3.OperationalError:
            pass  # 欄位已存在
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_logs_created_at ON ai_provider_logs(created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_logs_feature ON ai_provider_logs(feature)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_logs_provider ON ai_provider_logs(provider)"
        )
        conn.commit()
        conn.close()
    except Exception as e:  # noqa: BLE001
        logger.warning("⚠ 建立 ai_provider_logs 表失敗: %s", e)


def log_event(
    feature: str,
    provider: str,
    success: bool,
    latency_ms: Optional[float] = None,
    *,
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    fallback_used: bool = False,
    status_code: Optional[int] = None,
    error_type: Optional[str] = None,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
) -> None:
    """非阻塞寫入：佇列滿時直接丟棄，不影響業務流程。"""
    try:
        _ai_log_queue.put_nowait(
            (
                feature,
                provider,
                provider_name,
                model,
                1 if success else 0,
                1 if fallback_used else 0,
                round(latency_ms, 1) if latency_ms is not None else None,
                status_code,
                error_type,
                tokens_in,
                tokens_out,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
    except _queue.Full:
        pass


def _writer_loop() -> None:
    cleanup_counter = 0
    while True:
        batch: List[tuple] = []
        try:
            batch.append(_ai_log_queue.get(timeout=_LOG_FLUSH_INTERVAL))
        except _queue.Empty:
            pass

        while len(batch) < _LOG_BATCH_SIZE:
            try:
                batch.append(_ai_log_queue.get_nowait())
            except _queue.Empty:
                break

        if batch:
            try:
                conn = sqlite3.connect(config.DATABASE_PATH)
                conn.executemany(
                    """
                    INSERT INTO ai_provider_logs
                        (feature, provider, provider_name, model, success, fallback_used,
                         latency_ms, status_code, error_type, tokens_in, tokens_out, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch,
                )
                conn.commit()
                conn.close()
            except Exception:
                pass  # 紀錄失敗不影響業務

        cleanup_counter += 1
        if cleanup_counter >= 500:
            cleanup_counter = 0
            try:
                conn = sqlite3.connect(config.DATABASE_PATH)
                conn.execute(
                    "DELETE FROM ai_provider_logs WHERE created_at < datetime('now', '-30 days')"
                )
                conn.commit()
                conn.close()
            except Exception:
                pass


def start_writer() -> None:
    """啟動背景寫入 thread（重複呼叫無害）。"""
    global _writer_started
    with _writer_lock:
        if _writer_started:
            return
        ensure_table()
        t = threading.Thread(target=_writer_loop, daemon=True, name="ai-usage-writer")
        t.start()
        _writer_started = True


# ---------- 查詢輔助（admin 端使用） ----------


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_summary(days: int = 7) -> Dict[str, Any]:
    """彙總統計：總呼叫數、成功率、fallback 比例、平均延遲、各 provider/feature 拆分、每日序列。"""
    days = max(1, min(int(days), 90))
    where = "WHERE created_at >= datetime('now', ?, 'localtime')"
    arg = f"-{days} days"

    conn = _conn()
    try:
        # 總覽
        row = conn.execute(
            f"""
            SELECT
                COUNT(*)                                   AS total,
                SUM(success)                               AS success,
                SUM(CASE WHEN fallback_used=1 THEN 1 END)  AS fallback,
                AVG(latency_ms)                            AS avg_latency
            FROM ai_provider_logs {where}
            """,
            (arg,),
        ).fetchone()
        total = int(row["total"] or 0)
        success = int(row["success"] or 0)
        fallback = int(row["fallback"] or 0)
        avg_latency = float(row["avg_latency"] or 0.0)

        # 依 provider
        by_provider = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT provider, provider_name,
                       COUNT(*) AS calls,
                       SUM(success) AS success,
                       AVG(latency_ms) AS avg_latency
                FROM ai_provider_logs {where}
                GROUP BY provider, provider_name
                ORDER BY calls DESC
                """,
                (arg,),
            ).fetchall()
        ]

        # 依個別 API（provider + provider_name + model）拆分
        by_api = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT provider, provider_name, model,
                       COUNT(*) AS calls,
                       SUM(success) AS success,
                       SUM(CASE WHEN fallback_used=1 THEN 1 END) AS fallback,
                       AVG(latency_ms) AS avg_latency,
                       SUM(COALESCE(tokens_in, 0))  AS tokens_in,
                       SUM(COALESCE(tokens_out, 0)) AS tokens_out,
                       MAX(created_at)              AS last_used
                FROM ai_provider_logs {where}
                GROUP BY provider, provider_name, model
                ORDER BY calls DESC
                """,
                (arg,),
            ).fetchall()
        ]

        # 依 feature
        by_feature = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT feature,
                       COUNT(*) AS calls,
                       SUM(success) AS success,
                       SUM(CASE WHEN fallback_used=1 THEN 1 END) AS fallback,
                       AVG(latency_ms) AS avg_latency
                FROM ai_provider_logs {where}
                GROUP BY feature
                ORDER BY calls DESC
                """,
                (arg,),
            ).fetchall()
        ]

        # 每日序列
        daily = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT date(created_at) AS day,
                       COUNT(*) AS calls,
                       SUM(success) AS success,
                       SUM(CASE WHEN fallback_used=1 THEN 1 END) AS fallback
                FROM ai_provider_logs {where}
                GROUP BY day
                ORDER BY day ASC
                """,
                (arg,),
            ).fetchall()
        ]

        # 每日依 feature 拆分（供 stacked 圖表用）
        daily_by_feature = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT date(created_at) AS day,
                       feature,
                       COUNT(*) AS calls
                FROM ai_provider_logs {where}
                GROUP BY day, feature
                ORDER BY day ASC
                """,
                (arg,),
            ).fetchall()
        ]

        # 錯誤類型 Top
        errors = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT COALESCE(error_type, 'unknown') AS error_type,
                       COUNT(*) AS calls
                FROM ai_provider_logs {where} AND success = 0
                GROUP BY error_type
                ORDER BY calls DESC
                LIMIT 10
                """,
                (arg,),
            ).fetchall()
        ]
    finally:
        conn.close()

    return {
        "range_days": days,
        "total": total,
        "success": success,
        "fallback": fallback,
        "success_rate": (success / total) if total else 0.0,
        "fallback_rate": (fallback / total) if total else 0.0,
        "avg_latency_ms": round(avg_latency, 1),
        "by_api": by_api,
        "by_provider": by_provider,
        "by_feature": by_feature,
        "daily": daily,
        "daily_by_feature": daily_by_feature,
        "errors": errors,
    }


def query_recent(
    limit: int = 50,
    offset: int = 0,
    feature: Optional[str] = None,
    provider: Optional[str] = None,
    success: Optional[bool] = None,
) -> Dict[str, Any]:
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))
    conds: List[str] = []
    args: List[Any] = []
    if feature:
        conds.append("feature = ?")
        args.append(feature)
    if provider:
        conds.append("provider = ?")
        args.append(provider)
    if success is not None:
        conds.append("success = ?")
        args.append(1 if success else 0)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""

    conn = _conn()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM ai_provider_logs {where}", args
        ).fetchone()["c"]
        rows = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT id, feature, provider, provider_name, model, success, fallback_used,
                       latency_ms, status_code, error_type, tokens_in, tokens_out, created_at
                FROM ai_provider_logs {where}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (*args, limit, offset),
            ).fetchall()
        ]
    finally:
        conn.close()
    return {"total": int(total), "limit": limit, "offset": offset, "items": rows}
