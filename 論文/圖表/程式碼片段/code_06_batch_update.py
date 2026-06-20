# 程式碼片段 6：批次更新工作管理器 (scripts/batch_update.py)
# 用途：論文 3.7 節 — 自動化網路爬蟲資料更新

class BatchUpdateJob:
    """批次更新工作管理器（單例）"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.status = "idle"   # idle / running / paused / stopping / completed
        self.total = 0
        self.processed = 0
        self.updated = 0
        self.skipped = 0
        self.failed = 0
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # 預設不暫停
        self.delay = 0.5         # 請求間隔（原 3.0s → 優化至 0.5s）

    def start(self, db_path, delay=3.0, skip_cached=True, only_empty=True):
        """啟動批次更新（背景執行緒）"""
        self.reset()
        self.status = "running"
        self.delay = max(delay, 0.3)  # 最少 0.3 秒間隔
        self._thread = threading.Thread(
            target=self._run, args=(db_path,), daemon=True
        )
        self._thread.start()
        return True, "批次更新已啟動"

    def _run(self, db_path):
        """背景執行批次更新的主函式"""
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")    # 寫前日誌模式
        conn.execute("PRAGMA synchronous=NORMAL")  # 效能優化

        # 取得待更新藥物清單
        drugs = cursor.fetchall()
        self.total = len(drugs)

        # 共用 Playwright 瀏覽器實例（避免重複啟動）
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()

        for drug in drugs:
            # 檢查暫停 / 停止
            self._pause_event.wait()
            if self._stop_event.is_set():
                break

            # 爬取 NHI/TFDA 藥物資訊
            info = await scrape_nhi_drug_info(page, drug["chinese_name"])

            # 更新資料庫欄位
            if info:
                for nhi_field, db_field in NHI_FIELD_MAP.items():
                    if info.get(nhi_field):
                        cursor.execute(
                            f"UPDATE drugs SET {db_field}=? WHERE id=?",
                            (info[nhi_field], drug["id"])
                        )
                self.updated += 1

            self.processed += 1
            await asyncio.sleep(self.delay)  # 控制請求頻率
