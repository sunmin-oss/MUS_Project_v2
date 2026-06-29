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

        # 常見藥品縮寫展開（用於分詞匹配）
        _ABBREV = {
            "CAP": "CAPSULES", "CAPS": "CAPSULES",
            "TAB": "TABLETS", "TABS": "TABLETS",
            "F.C.T": "F.C. TABLETS", "F.C. T": "F.C. TABLETS", "FCT": "F.C. TABLETS",
            "INJ": "INJECTION", "SOL": "SOLUTION", "SYR": "SYRUP",
            "SUSP": "SUSPENSION", "CR": "CREAM", "OINT": "OINTMENT",
        }

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 策略1: 直接模糊搜尋 - 比對中文名稱、英文名稱、許可證字號
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

            # 策略2: 若無結果，嘗試去標點正規化匹配
            # 例如 "TFSUMIN FCT" 正規化後為 "TFSUMINFCT"，可匹配 "T.F.SU-MIN F.C. T"
            if not results:
                import re
                normalized_query = re.sub(r'[.\-\s\"\']', '', query.strip().upper())
                if len(normalized_query) >= 3:
                    cursor.execute(
                        f"""SELECT DISTINCT id, chinese_name, english_name, license_number,
                                   shape, color, indications, special_dosage_form, ingredient
                            FROM drugs
                            WHERE REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
                                    UPPER(english_name), '.', ''), '-', ''), ' ', ''), '"', ''), '''', '')
                                  LIKE ?
                            LIMIT ?""",
                        (f"%{normalized_query}%", limit),
                    )
                    for row in cursor.fetchall():
                        results.append(dict(row))

            # 策略3: 若仍無結果，嘗試展開縮寫後分詞 AND 匹配
            if not results:
                upper_query = query.strip().upper()
                words = upper_query.split()
                expanded_words = list(words)
                for i, w in enumerate(words):
                    if w in _ABBREV:
                        expanded_words[i] = _ABBREV[w]

                # 取長度>=3的詞做分詞匹配
                search_terms = [w for w in " ".join(expanded_words).split() if len(w) >= 3]
                if search_terms and len(search_terms) >= 2:
                    # 用詞幹匹配
                    stems = []
                    for w in search_terms:
                        if w.endswith("ULES"):
                            stems.append(w[:-2])
                        elif w.endswith("LETS"):
                            stems.append(w[:-1])
                        else:
                            stems.append(w)
                    conditions = " AND ".join(["UPPER(english_name) LIKE ?" for _ in stems])
                    params = [f"%{s}%" for s in stems] + [limit]
                    cursor.execute(
                        f"""SELECT DISTINCT id, chinese_name, english_name, license_number,
                                   shape, color, indications, special_dosage_form, ingredient
                            FROM drugs WHERE {conditions} LIMIT ?""",
                        params,
                    )
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

    def search_by_marking(self, marking: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        用刻印標記搜尋藥物（搜尋 label_front 和 label_back 欄位）

        參數:
            marking: 刻印標記文字，如 "YSP IBC"
            limit: 最多回傳筆數

        回傳:
            匹配的藥物列表
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 精確匹配優先，再模糊匹配
            search_param = f"%{marking}%"
            cursor.execute(
                """
                SELECT id, license_number, chinese_name, english_name,
                       shape, color, label_front, label_back, indications,
                       ingredient, manufacturer, dosage
                FROM drugs
                WHERE label_front LIKE ? OR label_back LIKE ?
                ORDER BY
                    CASE
                        WHEN label_front = ? THEN 0
                        WHEN label_back = ? THEN 0
                        ELSE 1
                    END
                LIMIT ?
            """,
                (search_param, search_param, marking, marking, limit),
            )

            results = [dict(row) for row in cursor.fetchall()]
            conn.close()

            logger.info(f"✓ 標記搜尋 '{marking}' 找到 {len(results)} 筆結果")
            return results

        except Exception as e:
            logger.error(f"✗ 標記搜尋失敗: {e}")
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

    # ============================================
    # 未比對藥物紀錄
    # ============================================

    def _ensure_unmatched_drugs_table(self):
        """確保 unmatched_drugs 表存在"""
        try:
            conn = self._get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS unmatched_drugs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    drug_name TEXT NOT NULL,
                    english_name TEXT,
                    license_number TEXT,
                    source TEXT DEFAULT 'prescription',
                    prescription_info TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    resolved_drug_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"✗ 建立 unmatched_drugs 表失敗: {e}")

    def add_unmatched_drug(
        self,
        drug_name: str,
        english_name: str = "",
        license_number: str = "",
        source: str = "prescription",
        prescription_info: Optional[Dict[str, Any]] = None,
    ) -> Optional[int]:
        """
        記錄一筆未比對到的藥物。若同名藥物已存在且為 pending，則累加次數。
        若藥物已在主資料庫或 unmatched_drugs 中已解決，則跳過不記錄。

        回傳: 記錄的 id，或 None（失敗/跳過）
        """
        import json
        import re

        self._ensure_unmatched_drugs_table()

        # 常見藥品縮寫展開
        _ABBREV = {
            "CAP": "CAPSULES", "CAPS": "CAPSULES",
            "TAB": "TABLETS", "TABS": "TABLETS",
            "F.C.T": "F.C. TABLETS", "F.C. T": "F.C. TABLETS", "FCT": "F.C. TABLETS",
            "INJ": "INJECTION", "SOL": "SOLUTION", "SYR": "SYRUP",
            "SUSP": "SUSPENSION", "CR": "CREAM", "OINT": "OINTMENT",
        }

        def _expand_name(name):
            """展開縮寫，回傳展開後的名稱列表"""
            names = [name]
            upper = name.upper()
            words = upper.split()
            for abbr, full in _ABBREV.items():
                if abbr in words:
                    expanded = upper.replace(abbr, full, 1)
                    names.append(expanded)
            return names

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # 先檢查藥物是否已在主資料庫 (drugs 表) 中
            # 策略1: 精確比對 + 不區分大小寫 + 展開縮寫後的 LIKE 比對
            search_names = _expand_name(drug_name)
            for sname in search_names:
                cursor.execute(
                    """SELECT id FROM drugs
                       WHERE UPPER(english_name) = UPPER(?)
                          OR UPPER(chinese_name) = UPPER(?)
                          OR UPPER(english_name) LIKE UPPER(?)
                       LIMIT 1""",
                    (sname, sname, f"%{sname}%"),
                )
                if cursor.fetchone():
                    conn.close()
                    logger.debug(f"⏭️ 未比對藥物跳過（已在資料庫中）: {drug_name}")
                    return None

            # 策略2: 分詞 AND 匹配 - 所有關鍵字都出現在 english_name 中
            # 例如 "FAMOTIDINE TABLETS" → english_name LIKE '%FAMOTIDINE%' AND english_name LIKE '%TABLET%'
            for sname in search_names:
                words = [w for w in sname.upper().split() if len(w) >= 3]
                if words:
                    # 對於 TABLETS/CAPSULES 等，用詞幹匹配 (去掉 S/ES)
                    stems = []
                    for w in words:
                        if w.endswith("ULES"):  # CAPSULES → CAPSUL
                            stems.append(w[:-2])
                        elif w.endswith("LETS"):  # TABLETS → TABLET
                            stems.append(w[:-1])
                        elif w.endswith("TION"):  # INJECTION → INJECTION
                            stems.append(w)
                        else:
                            stems.append(w)
                    conditions = " AND ".join(["UPPER(english_name) LIKE ?" for _ in stems])
                    params = [f"%{s}%" for s in stems]
                    cursor.execute(
                        f"SELECT id FROM drugs WHERE {conditions} LIMIT 1",
                        params,
                    )
                    if cursor.fetchone():
                        conn.close()
                        logger.debug(f"⏭️ 未比對藥物跳過（分詞匹配已在資料庫中）: {drug_name}")
                        return None

            # 檢查是否已有同名的 resolved/ignored 記錄（用 drug_name 或 english_name 比對）
            cursor.execute(
                """SELECT id FROM unmatched_drugs
                   WHERE (drug_name = ? OR english_name = ?) AND status IN ('resolved', 'ignored')""",
                (drug_name, drug_name),
            )
            if cursor.fetchone():
                conn.close()
                logger.debug(f"⏭️ 未比對藥物跳過（已解決/已忽略）: {drug_name}")
                return None

            # 檢查是否已有同名 pending 記錄
            cursor.execute(
                """SELECT id, occurrence_count FROM unmatched_drugs
                   WHERE (drug_name = ? OR english_name = ?) AND status = 'pending'""",
                (drug_name, drug_name),
            )
            existing = cursor.fetchone()

            if existing:
                record_id = existing[0]
                new_count = existing[1] + 1
                cursor.execute(
                    "UPDATE unmatched_drugs SET occurrence_count = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_count, record_id),
                )
                conn.commit()
                conn.close()
                logger.info(f"📝 未比對藥物已更新次數: {drug_name} (第 {new_count} 次)")
                return record_id
            else:
                pi_json = json.dumps(prescription_info, ensure_ascii=False) if prescription_info else None
                cursor.execute(
                    """
                    INSERT INTO unmatched_drugs (drug_name, english_name, license_number, source, prescription_info)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (drug_name, english_name, license_number, source, pi_json),
                )
                conn.commit()
                record_id = cursor.lastrowid
                conn.close()
                logger.info(f"📝 未比對藥物已記錄: {drug_name} (id={record_id})")
                return record_id

        except Exception as e:
            logger.error(f"✗ 記錄未比對藥物失敗: {e}")
            return None

    def get_unmatched_drugs(
        self, page: int = 1, per_page: int = 20, status: str = "", search: str = ""
    ) -> Dict[str, Any]:
        """
        取得未比對藥物列表（分頁 + 搜尋）。

        回傳: {"items": [...], "total": int, "page": int, "per_page": int}
        """
        import json

        self._ensure_unmatched_drugs_table()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            offset = (page - 1) * per_page

            where_clauses = []
            params = []
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            if search:
                where_clauses.append(
                    "(drug_name LIKE ? OR english_name LIKE ? OR license_number LIKE ?)"
                )
                like = f"%{search}%"
                params.extend([like, like, like])

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            cursor.execute(f"SELECT COUNT(*) FROM unmatched_drugs {where_sql}", params)
            total = cursor.fetchone()[0]
            cursor.execute(
                f"""
                SELECT * FROM unmatched_drugs {where_sql}
                ORDER BY occurrence_count DESC, updated_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [per_page, offset],
            )

            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            items = []
            for row in rows:
                item = dict(zip(columns, row))
                if item.get("prescription_info"):
                    try:
                        item["prescription_info"] = json.loads(item["prescription_info"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                items.append(item)

            conn.close()
            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
            }

        except Exception as e:
            logger.error(f"✗ 取得未比對藥物列表失敗: {e}")
            return {"items": [], "total": 0, "page": page, "per_page": per_page}

    def update_unmatched_drug_status(
        self, record_id: int, status: str, resolved_drug_id: Optional[int] = None
    ) -> bool:
        """更新未比對藥物狀態（resolved / ignored）"""
        self._ensure_unmatched_drugs_table()
        try:
            conn = self._get_connection()
            conn.execute(
                """
                UPDATE unmatched_drugs
                SET status = ?, resolved_drug_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, resolved_drug_id, record_id),
            )
            conn.commit()
            conn.close()
            logger.info(f"✓ 未比對藥物狀態已更新: id={record_id} → {status}")
            return True
        except Exception as e:
            logger.error(f"✗ 更新未比對藥物狀態失敗: {e}")
            return False

    # ============================================
    # 辨識歷史紀錄
    # ============================================

    def _ensure_recognition_history_table(self):
        """確保 recognition_history 表存在"""
        try:
            conn = self._get_connection()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recognition_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    drug_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rh_filename ON recognition_history(filename)
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"✗ 建立 recognition_history 表失敗: {e}")

    def save_recognition_history(
        self, filename: str, mode: str, result: Any, drug_count: int = 0
    ):
        """儲存一筆辨識歷史"""
        import json

        self._ensure_recognition_history_table()
        try:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO recognition_history (filename, mode, result_json, drug_count)
                VALUES (?, ?, ?, ?)
                """,
                (filename, mode, json.dumps(result, ensure_ascii=False, default=str), drug_count),
            )
            conn.commit()
            conn.close()
            logger.info(f"✓ 辨識歷史已儲存: {filename} ({mode}, {drug_count} 筆)")
        except Exception as e:
            logger.error(f"✗ 儲存辨識歷史失敗: {e}")

    def get_recognition_history(self, filename: str) -> Optional[Dict[str, Any]]:
        """依檔名查詢最近一筆辨識結果"""
        import json

        self._ensure_recognition_history_table()
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, filename, mode, result_json, drug_count, created_at
                FROM recognition_history
                WHERE filename = ?
                ORDER BY created_at DESC LIMIT 1
                """,
                (filename,),
            )
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    "id": row[0],
                    "filename": row[1],
                    "mode": row[2],
                    "result": json.loads(row[3]),
                    "drug_count": row[4],
                    "created_at": row[5],
                }
            return None
        except Exception as e:
            logger.error(f"✗ 查詢辨識歷史失敗: {e}")
            return None
