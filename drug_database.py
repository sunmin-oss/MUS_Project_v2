"""
==============================================
簡化版藥物資料庫查詢模組 (drug_database.py)
==============================================

【功能說明】
簡化版資料庫查詢模組，支援使用現有的 MUS_Project 資料庫。

【功能】
1. 按名稱搜尋藥物
2. 按 ID 查詢藥物詳細資訊
3. 支援模糊搜尋

【作者】MUS2 團隊
【日期】2025
"""

import sqlite3
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DrugDatabase:
    """簡化版藥物資料庫查詢類"""

    def __init__(self, db_path: str = "drug_recognition.db"):
        """
        初始化資料庫

        參數:
            db_path: SQLite 資料庫檔案路徑 (可以是相對路徑或絕對路徑)
        """
        # 如果是相對路徑，轉換為絕對路徑（相對於此檔案所在目錄）
        if not Path(db_path).is_absolute():
            script_dir = Path(__file__).parent
            db_path = str(script_dir / db_path)

        self.db_path = db_path
        self._check_database_exists()

    def _check_database_exists(self):
        """檢查資料庫是否存在"""
        if not Path(self.db_path).exists():
            logger.warning(f"⚠ 資料庫不存在: {self.db_path}")
            logger.info("💡 請複製 MUS_Project/drug_recognition.db 到 MUS2 目錄")

    def _get_connection(self) -> sqlite3.Connection:
        """取得資料庫連線"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 以字典方式返回查詢結果
        return conn

    def search_by_name(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        按名稱搜尋藥物

        參數:
            query: 搜尋關鍵字
            limit: 最多回傳數量

        回傳:
            藥物資訊列表
        """
        if not query or not query.strip():
            return []

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 模糊搜尋 - 比對中文名稱、英文名稱、許可證字號
            search_param = f"%{query}%"
            cursor.execute(
                """
                SELECT DISTINCT
                    id,
                    chinese_name,
                    english_name,
                    license_number,
                    shape,
                    color,
                    indications,
                    special_dosage_form,
                    ingredient
                FROM drugs
                WHERE 
                    chinese_name LIKE ? OR
                    english_name LIKE ? OR
                    license_number LIKE ?
                LIMIT ?
            """,
                (search_param, search_param, search_param, limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            conn.close()
            logger.info(f"✓ 搜尋 '{query}' 找到 {len(results)} 個結果")
            return results

        except sqlite3.OperationalError as e:
            logger.debug(f"ℹ 資料庫結構與預期不同，切換至備用查詢模式: {e}")
            # 如果表結構不同，嘗試替代查詢
            return self._search_by_name_fallback(query, limit)
        except Exception as e:
            logger.error(f"✗ 搜尋出錯: {e}")
            return []

    def _search_by_name_fallback(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """備選查詢方法"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 取得表結構
            cursor.execute("PRAGMA table_info(drugs)")
            columns = [row[1] for row in cursor.fetchall()]

            # 組建查詢
            search_param = f"%{query}%"
            conditions = []

            for col in ["chinese_name", "english_name", "name", "license_number"]:
                if col in columns:
                    conditions.append(f"{col} LIKE ?")

            if not conditions:
                logger.warning("⚠ 無法確定正確的表結構")
                return []

            where_clause = " OR ".join(conditions)
            sql = f"SELECT * FROM drugs WHERE {where_clause} LIMIT ?"

            cursor.execute(sql, tuple([search_param] * len(conditions) + [limit]))

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            conn.close()
            return results

        except Exception as e:
            logger.error(f"✗ 備選查詢失敗: {e}")
            return []

    def get_drug_by_id(self, drug_id: int) -> Optional[Dict[str, Any]]:
        """
        按 ID 查詢藥物詳細資訊

        參數:
            drug_id: 藥物 ID

        回傳:
            藥物詳細資訊或 None
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            try:
                cursor.execute(
                    """
                    SELECT *
                    FROM drugs
                    WHERE drug_id = ?
                    LIMIT 1
                """,
                    (drug_id,),
                )
            except sqlite3.OperationalError:
                # 兼容舊版結構，如果沒有 drug_id，嘗試使用 id
                cursor.execute(
                    """
                    SELECT *
                    FROM drugs
                    WHERE id = ?
                    LIMIT 1
                """,
                    (drug_id,),
                )

            row = cursor.fetchone()
            conn.close()

            if row:
                return dict(row)
            return None

        except Exception as e:
            logger.error(f"✗ 查詢藥物詳細資訊失敗: {e}")
            return None

    def get_all_columns(self) -> List[str]:
        """取得 drugs 表的所有列名"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(drugs)")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            return columns
        except Exception as e:
            logger.error(f"✗ 無法取得表結構: {e}")
            return []

    def get_drug_features_for_rag(self, sample_size: int = 500) -> str:
        """
        取得藥物特徵列表用於 RAG

        參數:
            sample_size: 每批抽取的樣本數

        回傳:
            格式化的藥物特徵字符串，供 AI 用於匹配
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 先取得總數
            cursor.execute("SELECT COUNT(*) FROM drugs")
            total_count = cursor.fetchone()[0]

            # 分批取得藥物（避免內存溢出）
            # 這次先取前 sample_size 個具有完整信息的藥物
            cursor.execute(
                """
                SELECT id, license_number, chinese_name, english_name, 
                       shape, color, special_dosage_form, label_front, label_back
                FROM drugs
                WHERE chinese_name IS NOT NULL AND length(chinese_name) > 0
                LIMIT ?
            """,
                (sample_size,),
            )

            drugs = cursor.fetchall()
            conn.close()

            if not drugs:
                logger.warning("⚠ 無法取得藥物特徵列表")
                return ""

            # 組織成精簡格式（減少 token 數量，提升 API 回應速度）
            # 格式: ID|標記正面/背面|中文名|形狀|顏色
            drug_list = []
            for drug in drugs:
                (
                    drug_id,
                    license,
                    cn_name,
                    en_name,
                    shape,
                    color,
                    form,
                    label_front,
                    label_back,
                ) = drug

                # 精簡格式：只保留辨識關鍵欄位
                marks = ""
                if label_front and label_back:
                    marks = f"{label_front}/{label_back}"
                elif label_front:
                    marks = label_front
                elif label_back:
                    marks = label_back

                parts = [str(drug_id), marks, cn_name or ""]
                if shape:
                    parts.append(shape)
                if color:
                    parts.append(color)

                drug_list.append("|".join(parts))

            logger.info(f"✓ RAG 藥物清單包含 {len(drug_list)} 個藥物")
            return "\n".join(drug_list)

        except Exception as e:
            logger.error(f"✗ 無法取得 RAG 藥物清單: {e}")
            return ""

    def get_drug_images(self, drug_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        取得藥物的圖片列表

        參數:
            drug_id: 藥物 ID
            limit: 最多返回圖片數

        回傳:
            圖片信息列表 [{'id': 1, 'filename': '...', 'path': '...', 'order': 1}, ...]
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, image_filename, image_path, image_order
                FROM drug_images
                WHERE drug_id = ?
                ORDER BY image_order ASC
                LIMIT ?
            """,
                (drug_id, limit),
            )

            images = []
            for row in cursor.fetchall():
                images.append(
                    {
                        "id": row[0],
                        "filename": row[1],
                        "path": row[2],
                        "order": row[3],
                    }
                )

            conn.close()
            return images

        except Exception as e:
            logger.error(f"✗ 取得藥物圖片失敗: {e}")
            return []

    # ============================================
    # NHI/TFDA 快取機制
    # ============================================

    def _ensure_nhi_cache_table(self):
        """確保 nhi_cache 表存在"""
        try:
            conn = self._get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nhi_cache (
                    drug_id INTEGER PRIMARY KEY,
                    search_name TEXT NOT NULL,
                    nhi_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"✗ 建立 nhi_cache 表失敗: {e}")

    def get_nhi_cache(
        self, drug_id: int, max_age_days: int = 7
    ) -> Optional[Dict[str, Any]]:
        """
        從快取取得 NHI/TFDA 資料

        參數:
            drug_id: 藥物 ID
            max_age_days: 快取有效天數（預設 7 天）

        回傳:
            快取的 NHI 資料，或 None（無快取或已過期）
        """
        import json

        self._ensure_nhi_cache_table()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT nhi_data, updated_at FROM nhi_cache
                WHERE drug_id = ?
                AND updated_at >= datetime('now', ?)
            """,
                (drug_id, f"-{max_age_days} days"),
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                logger.info(f"✓ NHI 快取命中 (drug_id={drug_id})")
                return json.loads(row[0])
            return None

        except Exception as e:
            logger.error(f"✗ 讀取 NHI 快取失敗: {e}")
            return None

    def set_nhi_cache(self, drug_id: int, search_name: str, nhi_data: Dict[str, Any]):
        """
        儲存 NHI/TFDA 資料到快取

        參數:
            drug_id: 藥物 ID
            search_name: 搜尋使用的關鍵字
            nhi_data: 從爬蟲取得的 NHI 資料字典
        """
        import json

        self._ensure_nhi_cache_table()
        try:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO nhi_cache (drug_id, search_name, nhi_data, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(drug_id) DO UPDATE SET
                    search_name = excluded.search_name,
                    nhi_data = excluded.nhi_data,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (drug_id, search_name, json.dumps(nhi_data, ensure_ascii=False)),
            )
            conn.commit()
            conn.close()
            logger.info(f"✓ NHI 快取已儲存 (drug_id={drug_id}, name={search_name})")
        except Exception as e:
            logger.error(f"✗ 儲存 NHI 快取失敗: {e}")
