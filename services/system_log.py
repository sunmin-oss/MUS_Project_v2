"""
系統應用程式日誌 (system_logs)

把 Python logging 的訊息透過 SQLiteLogHandler 寫入 system_logs 表，
讓後台「Log 紀錄」頁可以統一檢視。採背景批次寫入避免阻塞主流程。
"""

from __future__ import annotations

import logging
import queue as _queue
import sqlite3
import threading
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

from config import config


_LOG_FLUSH_INTERVAL = 2
_LOG_BATCH_SIZE = 100
_log_queue: "_queue.Queue[tuple]" = _queue.Queue(maxsize=5000)
_writer_started = False
_writer_lock = threading.Lock()

# 不要把這些頻繁吵雜的 logger 寫入資料庫
_NOISY_LOGGERS = {
    "werkzeug",
    "apscheduler",
    "apscheduler.scheduler",
    "apscheduler.executors.default",
    "urllib3",
    "urllib3.connectionpool",
    "PIL",
}


def ensure_table() -> None:
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                logger TEXT,
                message TEXT NOT NULL,
                module TEXT,
                func TEXT,
                lineno INTEGER,
                exc_info TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sys_logs_created_at ON system_logs(created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sys_logs_level ON system_logs(level)"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass  # 寫不進就吃掉，避免 logging 反過來把系統打掛


def _writer_loop() -> None:
    cleanup_counter = 0
    while True:
        batch: List[tuple] = []
        try:
            batch.append(_log_queue.get(timeout=_LOG_FLUSH_INTERVAL))
        except _queue.Empty:
            pass

        while len(batch) < _LOG_BATCH_SIZE:
            try:
                batch.append(_log_queue.get_nowait())
            except _queue.Empty:
                break

        if batch:
            try:
                conn = sqlite3.connect(config.DATABASE_PATH)
                conn.executemany(
                    """
                    INSERT INTO system_logs
                        (level, logger, message, module, func, lineno, exc_info, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    batch,
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

        cleanup_counter += 1
        if cleanup_counter >= 500:
            cleanup_counter = 0
            try:
                conn = sqlite3.connect(config.DATABASE_PATH)
                conn.execute(
                    "DELETE FROM system_logs WHERE created_at < datetime('now', '-30 days')"
                )
                conn.commit()
                conn.close()
            except Exception:
                pass


class SQLiteLogHandler(logging.Handler):
    """把 LogRecord 推進佇列，由背景 thread 批次寫入 system_logs。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if record.name in _NOISY_LOGGERS:
                return
            for noisy in _NOISY_LOGGERS:
                if record.name.startswith(noisy + "."):
                    return

            msg = record.getMessage()
            exc_text: Optional[str] = None
            if record.exc_info:
                exc_text = "".join(traceback.format_exception(*record.exc_info))[:4000]

            _log_queue.put_nowait(
                (
                    record.levelname,
                    record.name,
                    msg[:4000],
                    record.module,
                    record.funcName,
                    record.lineno,
                    exc_text,
                    datetime.fromtimestamp(record.created).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                )
            )
        except _queue.Full:
            pass
        except Exception:
            pass  # logging handler 內部不能再拋例外


def install(level: int = logging.INFO) -> None:
    """安裝 SQLiteLogHandler 到 root logger（重複呼叫無害）。"""
    global _writer_started
    with _writer_lock:
        if _writer_started:
            return
        ensure_table()
        root = logging.getLogger()
        # 避免重複安裝（重啟 Flask reloader 時）
        if any(isinstance(h, SQLiteLogHandler) for h in root.handlers):
            _writer_started = True
            return
        handler = SQLiteLogHandler(level=level)
        handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(handler)

        t = threading.Thread(target=_writer_loop, daemon=True, name="system-log-writer")
        t.start()
        _writer_started = True


# ---------- 查詢輔助 ----------


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def query_recent(
    limit: int = 100,
    offset: int = 0,
    level: Optional[str] = None,
    keyword: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Dict[str, Any]:
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    conds: List[str] = []
    args: List[Any] = []
    if level:
        conds.append("level = ?")
        args.append(level.upper())
    if keyword:
        conds.append("(message LIKE ? OR logger LIKE ?)")
        args.extend([f"%{keyword}%", f"%{keyword}%"])
    if start:
        conds.append("created_at >= ?")
        args.append(start)
    if end:
        conds.append("created_at <= ?")
        args.append(end)
    where = ("WHERE " + " AND ".join(conds)) if conds else ""

    conn = _conn()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) AS c FROM system_logs {where}", args
        ).fetchone()["c"]
        rows = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT id, level, logger, message, module, func, lineno, exc_info, created_at
                FROM system_logs {where}
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (*args, limit, offset),
            ).fetchall()
        ]
    finally:
        conn.close()
    return {"total": int(total), "limit": limit, "offset": offset, "items": rows}
