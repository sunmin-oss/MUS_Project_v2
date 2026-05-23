"""
==============================================
批次更新藥物資料模組 (batch_update.py)
==============================================

【功能說明】
從健保署/TFDA 平台批次爬取所有藥物資訊，更新本地資料庫。
支援背景執行、進度追蹤、暫停/繼續/停止。

【欄位對應】NHI 爬蟲欄位 → drugs 表欄位
- 適應症 → indications
- 主成分略述 → ingredient
- 劑型 → special_dosage_form
- 藥品類別 → category
- 製造廠名稱 → manufacturer
- 有效日期 → expiry_info
- 包裝 → (存入 nhi_cache)

【作者】MUS2 團隊
【日期】2025
"""

import asyncio
import threading
import sqlite3
import json
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# NHI 欄位 → drugs 表欄位對應
NHI_FIELD_MAP = {
    "適應症": "indications",
    "主成分略述": "ingredient",
    "劑型": "special_dosage_form",
    "藥品類別": "category",
    "製造廠名稱": "manufacturer",
    "有效日期": "expiry_info",
}


class BatchUpdateJob:
    """批次更新工作管理器（單例）"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.status = "idle"  # idle / running / paused / stopping / completed / error
        self.total = 0
        self.processed = 0
        self.updated = 0
        self.skipped = 0
        self.failed = 0
        self.current_drug = ""
        self.start_time = None
        self.end_time = None
        self.errors = []  # 最近的錯誤（最多保留 50 條）
        self.log = []  # 最近的日誌（最多保留 100 條）
        self._thread = None
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 預設不暫停
        # 設定選項
        self.delay = 3.0  # 每次請求間隔（秒）
        self.skip_cached = True  # 跳過已有快取的
        self.only_empty = True  # 只更新空欄位的藥物

    @property
    def progress(self):
        if self.total == 0:
            return 0
        return round(self.processed / self.total * 100, 1)

    @property
    def elapsed(self):
        if not self.start_time:
            return 0
        end = self.end_time or time.time()
        return round(end - self.start_time, 1)

    @property
    def eta_seconds(self):
        if self.processed == 0 or not self.start_time:
            return 0
        elapsed = time.time() - self.start_time
        rate = self.processed / elapsed
        remaining = self.total - self.processed
        return round(remaining / rate) if rate > 0 else 0

    def _log(self, msg):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
        self.log.append(entry)
        if len(self.log) > 100:
            self.log = self.log[-100:]
        logger.info(f"[BatchUpdate] {msg}")

    def _add_error(self, drug_id, name, error):
        self.errors.append(
            {
                "drug_id": drug_id,
                "name": name,
                "error": str(error),
                "time": datetime.now().strftime("%H:%M:%S"),
            }
        )
        if len(self.errors) > 50:
            self.errors = self.errors[-50:]

    def get_status(self):
        return {
            "status": self.status,
            "total": self.total,
            "processed": self.processed,
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "progress": self.progress,
            "current_drug": self.current_drug,
            "elapsed": self.elapsed,
            "eta_seconds": self.eta_seconds,
            "errors": self.errors[-10:],
            "log": self.log[-20:],
            "delay": self.delay,
            "skip_cached": self.skip_cached,
            "only_empty": self.only_empty,
        }

    def start(self, db_path, delay=3.0, skip_cached=True, only_empty=True):
        """啟動批次更新"""
        if self.status == "running":
            return False, "已有工作在執行中"
        if self.status == "paused":
            return False, "工作已暫停，請使用繼續功能"

        self.reset()
        self.status = "running"
        self.delay = max(delay, 1.0)  # 最少 1 秒
        self.skip_cached = skip_cached
        self.only_empty = only_empty
        self.start_time = time.time()
        self._stop_event.clear()
        self._pause_event.set()

        self._thread = threading.Thread(target=self._run, args=(db_path,), daemon=True)
        self._thread.start()
        return True, "批次更新已啟動"

    def stop(self):
        """停止批次更新"""
        if self.status not in ("running", "paused"):
            return False, "沒有正在執行的工作"
        self.status = "stopping"
        self._stop_event.set()
        self._pause_event.set()  # 解除暫停讓它能結束
        self._log("收到停止指令，等待目前工作完成...")
        return True, "正在停止..."

    def pause(self):
        """暫停批次更新"""
        if self.status != "running":
            return False, "只能暫停執行中的工作"
        self._pause_event.clear()
        self.status = "paused"
        self._log("已暫停")
        return True, "已暫停"

    def resume(self):
        """繼續批次更新"""
        if self.status != "paused":
            return False, "沒有已暫停的工作"
        self._pause_event.set()
        self.status = "running"
        self._log("已繼續執行")
        return True, "已繼續"

    def _run(self, db_path):
        """背景執行批次更新的主函式"""
        from scripts.nhi_crawler import scrape_nhi_drug_info

        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 取得要更新的藥物清單
            if self.only_empty:
                cursor.execute("""
                    SELECT id, chinese_name, english_name FROM drugs
                    WHERE chinese_name IS NOT NULL AND length(chinese_name) > 0
                    AND (indications IS NULL OR indications = ''
                         OR ingredient IS NULL OR ingredient = '')
                    ORDER BY id
                """)
            else:
                cursor.execute("""
                    SELECT id, chinese_name, english_name FROM drugs
                    WHERE chinese_name IS NOT NULL AND length(chinese_name) > 0
                    ORDER BY id
                """)

            drugs = [dict(row) for row in cursor.fetchall()]
            self.total = len(drugs)
            self._log(f"共 {self.total} 筆藥物待更新")

            if self.total == 0:
                self.status = "completed"
                self._log("沒有需要更新的藥物")
                conn.close()
                return

            # 取得已有快取的 ID
            cached_ids = set()
            if self.skip_cached:
                try:
                    cursor.execute(
                        "SELECT drug_id FROM nhi_cache WHERE updated_at >= datetime('now', '-7 days')"
                    )
                    cached_ids = {row[0] for row in cursor.fetchall()}
                    self._log(f"已有 {len(cached_ids)} 筆有效快取")
                except sqlite3.OperationalError:
                    pass

            conn.close()

            # 建立 asyncio event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            for drug in drugs:
                # 檢查停止
                if self._stop_event.is_set():
                    self._log("已停止執行")
                    break

                # 等待暫停解除
                self._pause_event.wait()

                drug_id = drug["id"]
                name = drug["chinese_name"]
                self.current_drug = f"[{drug_id}] {name}"

                # 跳過已快取的
                if self.skip_cached and drug_id in cached_ids:
                    self.skipped += 1
                    self.processed += 1
                    continue

                try:
                    # 爬取 NHI 資訊
                    result = loop.run_until_complete(scrape_nhi_drug_info(name))

                    if result and result.get("status") == "success":
                        details = result.get("details", {})

                        if details and len(details) > 2:
                            # 更新 drugs 表
                            self._update_drug_fields(db_path, drug_id, details)
                            # 更新 NHI 快取
                            self._update_cache(db_path, drug_id, name, details)
                            self.updated += 1
                            self._log(
                                f"✓ [{drug_id}] {name} — 取得 {len(details)} 個欄位"
                            )
                        else:
                            self.skipped += 1
                            self._log(f"⊘ [{drug_id}] {name} — 無額外資訊")
                    else:
                        error_msg = (
                            result.get("error", "未知錯誤") if result else "無回應"
                        )
                        self.failed += 1
                        self._add_error(drug_id, name, error_msg)
                        self._log(f"✗ [{drug_id}] {name} — {error_msg}")

                except Exception as e:
                    self.failed += 1
                    self._add_error(drug_id, name, str(e))
                    self._log(f"✗ [{drug_id}] {name} — 例外: {e}")

                self.processed += 1

                # 延遲，避免被封鎖
                if not self._stop_event.is_set():
                    time.sleep(self.delay)

            loop.close()

            if self._stop_event.is_set():
                self.status = "stopped"
            else:
                self.status = "completed"

            self.end_time = time.time()
            self._log(
                f"完成！更新 {self.updated} 筆、跳過 {self.skipped} 筆、失敗 {self.failed} 筆，耗時 {self.elapsed} 秒"
            )

        except Exception as e:
            self.status = "error"
            self.end_time = time.time()
            self._log(f"批次更新發生嚴重錯誤: {e}")
            logger.error(f"[BatchUpdate] 嚴重錯誤: {e}", exc_info=True)

    def _update_drug_fields(self, db_path, drug_id, details):
        """從 NHI 資料更新 drugs 表欄位"""
        try:
            conn = sqlite3.connect(db_path)
            updates = []
            values = []

            for nhi_field, db_field in NHI_FIELD_MAP.items():
                if nhi_field in details and details[nhi_field]:
                    value = details[nhi_field].strip()
                    if value and value != "--":
                        updates.append(f"{db_field} = ?")
                        values.append(value)

            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                values.append(drug_id)
                set_clause = ", ".join(updates)
                conn.execute(f"UPDATE drugs SET {set_clause} WHERE id = ?", values)
                conn.commit()

            conn.close()
        except Exception as e:
            logger.error(f"✗ 更新 drug {drug_id} 欄位失敗: {e}")

    def _update_cache(self, db_path, drug_id, search_name, details):
        """更新 NHI 快取"""
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nhi_cache (
                    drug_id INTEGER PRIMARY KEY,
                    search_name TEXT NOT NULL,
                    nhi_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute(
                """
                INSERT INTO nhi_cache (drug_id, search_name, nhi_data, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(drug_id) DO UPDATE SET
                    search_name = excluded.search_name,
                    nhi_data = excluded.nhi_data,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (drug_id, search_name, json.dumps(details, ensure_ascii=False)),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"✗ 更新快取 {drug_id} 失敗: {e}")


# 全域單例
batch_job = BatchUpdateJob()
