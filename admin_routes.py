"""
==============================================
管理員 API 路由 (admin_routes.py)
==============================================

【功能說明】
提供管理員後台所需的所有 API 端點，包括：
1. 儀表板統計資料
2. 藥物 CRUD 管理
3. NHI 快取管理
4. 上傳檔案管理
5. 系統設定
6. API 使用統計

【作者】MUS2 團隊
【日期】2025
"""

from flask import Blueprint, request, jsonify, send_from_directory
import os
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def get_db_connection(db_path):
    """取得資料庫連線"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================
# 管理員前端頁面
# ============================================


@admin_bp.route("/", methods=["GET"])
def admin_page():
    """提供管理員前端頁面"""
    return send_from_directory(os.path.dirname(__file__), "admin.html")


# ============================================
# 儀表板 API
# ============================================


@admin_bp.route("/api/dashboard", methods=["GET"])
def dashboard():
    """取得儀表板統計資料"""
    try:
        from config import config

        conn = get_db_connection(config.DATABASE_PATH)
        cursor = conn.cursor()

        # 藥物總數
        cursor.execute("SELECT COUNT(*) FROM drugs")
        drug_count = cursor.fetchone()[0]

        # 圖片總數
        try:
            cursor.execute("SELECT COUNT(*) FROM drug_images")
            image_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            image_count = 0

        # NHI 快取筆數
        try:
            cursor.execute("SELECT COUNT(*) FROM nhi_cache")
            cache_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            cache_count = 0

        # API 使用統計
        try:
            cursor.execute("SELECT COUNT(*) FROM api_logs")
            total_requests = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM api_logs WHERE created_at >= datetime('now', '-1 day')"
            )
            today_requests = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM api_logs WHERE endpoint LIKE '%recognize%'"
            )
            recognize_count = cursor.fetchone()[0]
            cursor.execute(
                "SELECT COUNT(*) FROM api_logs WHERE endpoint LIKE '%search%'"
            )
            search_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            total_requests = 0
            today_requests = 0
            recognize_count = 0
            search_count = 0

        # uploads 資料夾大小
        uploads_path = Path(config.UPLOAD_FOLDER)
        uploads_size = 0
        uploads_file_count = 0
        if uploads_path.exists():
            for f in uploads_path.iterdir():
                if f.is_file():
                    uploads_size += f.stat().st_size
                    uploads_file_count += 1

        # 最近 API 請求
        recent_logs = []
        try:
            cursor.execute("""
                SELECT endpoint, method, status_code, duration_ms, created_at, query_params
                FROM api_logs ORDER BY created_at DESC LIMIT 10
            """)
            for row in cursor.fetchall():
                recent_logs.append(dict(row))
        except sqlite3.OperationalError:
            pass

        conn.close()

        return jsonify(
            {
                "success": True,
                "stats": {
                    "drug_count": drug_count,
                    "image_count": image_count,
                    "cache_count": cache_count,
                    "total_requests": total_requests,
                    "today_requests": today_requests,
                    "recognize_count": recognize_count,
                    "search_count": search_count,
                    "uploads_size_mb": round(uploads_size / (1024 * 1024), 2),
                    "uploads_file_count": uploads_file_count,
                },
                "recent_logs": recent_logs,
            }
        )
    except Exception as e:
        logger.error(f"✗ 儀表板錯誤: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# 藥物管理 API
# ============================================


@admin_bp.route("/api/drugs", methods=["GET"])
def list_drugs():
    """取得藥物列表（分頁 + 搜尋）"""
    try:
        from config import config

        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        search = request.args.get("search", "").strip()
        offset = (page - 1) * per_page

        conn = get_db_connection(config.DATABASE_PATH)
        cursor = conn.cursor()

        if search:
            search_param = f"%{search}%"
            cursor.execute(
                "SELECT COUNT(*) FROM drugs WHERE chinese_name LIKE ? OR english_name LIKE ? OR license_number LIKE ?",
                (search_param, search_param, search_param),
            )
            total = cursor.fetchone()[0]
            cursor.execute(
                """
                SELECT * FROM drugs
                WHERE chinese_name LIKE ? OR english_name LIKE ? OR license_number LIKE ?
                ORDER BY id LIMIT ? OFFSET ?
            """,
                (search_param, search_param, search_param, per_page, offset),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM drugs")
            total = cursor.fetchone()[0]
            cursor.execute(
                "SELECT * FROM drugs ORDER BY id LIMIT ? OFFSET ?", (per_page, offset)
            )

        drugs = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify(
            {
                "success": True,
                "drugs": drugs,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": (total + per_page - 1) // per_page,
            }
        )
    except Exception as e:
        logger.error(f"✗ 列表錯誤: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/drugs", methods=["POST"])
def create_drug():
    """新增藥物"""
    try:
        from config import config

        data = request.get_json()
        conn = get_db_connection(config.DATABASE_PATH)

        columns = []
        values = []
        for key in [
            "chinese_name",
            "english_name",
            "license_number",
            "shape",
            "color",
            "usage",
            "formulation",
            "dosage_strength",
            "special_dosage_form",
        ]:
            if data.get(key):
                columns.append(key)
                values.append(data[key])

        if not columns:
            return jsonify({"success": False, "error": "至少需要一個欄位"}), 400

        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        conn.execute(f"INSERT INTO drugs ({col_names}) VALUES ({placeholders})", values)
        conn.commit()
        drug_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        return jsonify({"success": True, "drug_id": drug_id, "message": "藥物已新增"})
    except Exception as e:
        logger.error(f"✗ 新增藥物錯誤: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/drugs/<int:drug_id>", methods=["PUT"])
def update_drug(drug_id):
    """更新藥物"""
    try:
        from config import config

        data = request.get_json()
        conn = get_db_connection(config.DATABASE_PATH)

        updates = []
        values = []
        for key in [
            "chinese_name",
            "english_name",
            "license_number",
            "shape",
            "color",
            "usage",
            "formulation",
            "dosage_strength",
            "special_dosage_form",
        ]:
            if key in data:
                updates.append(f"{key} = ?")
                values.append(data[key])

        if not updates:
            return jsonify({"success": False, "error": "無更新欄位"}), 400

        values.append(drug_id)
        set_clause = ", ".join(updates)
        conn.execute(f"UPDATE drugs SET {set_clause} WHERE id = ?", values)
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "藥物已更新"})
    except Exception as e:
        logger.error(f"✗ 更新藥物錯誤: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/drugs/<int:drug_id>", methods=["DELETE"])
def delete_drug(drug_id):
    """刪除藥物"""
    try:
        from config import config

        conn = get_db_connection(config.DATABASE_PATH)
        conn.execute("DELETE FROM drugs WHERE id = ?", (drug_id,))
        try:
            conn.execute("DELETE FROM drug_images WHERE drug_id = ?", (drug_id,))
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("DELETE FROM nhi_cache WHERE drug_id = ?", (drug_id,))
        except sqlite3.OperationalError:
            pass
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "藥物已刪除"})
    except Exception as e:
        logger.error(f"✗ 刪除藥物錯誤: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/drugs/export", methods=["GET"])
def export_drugs():
    """匯出藥物為 CSV"""
    try:
        import csv
        import io
        from flask import Response
        from config import config

        conn = get_db_connection(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM drugs ORDER BY id")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(list(row))

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=drugs_export.csv"},
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# NHI 快取管理 API
# ============================================


@admin_bp.route("/api/cache", methods=["GET"])
def list_cache():
    """列出所有 NHI 快取"""
    try:
        from config import config

        conn = get_db_connection(config.DATABASE_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT c.drug_id, c.search_name, c.updated_at, c.nhi_data,
                       d.chinese_name, d.english_name
                FROM nhi_cache c
                LEFT JOIN drugs d ON c.drug_id = d.id
                ORDER BY c.updated_at DESC
            """)
            caches = []
            for row in cursor.fetchall():
                r = dict(row)
                nhi = json.loads(r.get("nhi_data", "{}"))
                r["nhi_fields"] = len(nhi)
                r["has_indication"] = "適應症" in nhi
                del r["nhi_data"]  # 不傳完整資料到列表
                caches.append(r)
        except sqlite3.OperationalError:
            caches = []

        conn.close()
        return jsonify({"success": True, "caches": caches, "total": len(caches)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/cache/<int:drug_id>", methods=["DELETE"])
def delete_cache(drug_id):
    """刪除指定藥物的快取"""
    try:
        from config import config

        conn = get_db_connection(config.DATABASE_PATH)
        conn.execute("DELETE FROM nhi_cache WHERE drug_id = ?", (drug_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "快取已刪除"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/cache/clear", methods=["POST"])
def clear_expired_cache():
    """清除過期快取"""
    try:
        from config import config

        days = request.get_json().get("days", 7) if request.is_json else 7
        conn = get_db_connection(config.DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM nhi_cache WHERE updated_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return jsonify(
            {
                "success": True,
                "deleted": deleted,
                "message": f"已清除 {deleted} 筆過期快取",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/cache/refresh/<int:drug_id>", methods=["POST"])
def refresh_cache(drug_id):
    """手動重新爬取指定藥物的 NHI 資訊"""
    try:
        from config import config

        conn = get_db_connection(config.DATABASE_PATH)
        cursor = conn.cursor()

        # 取得藥物名稱
        cursor.execute(
            "SELECT chinese_name, english_name FROM drugs WHERE id = ?", (drug_id,)
        )
        drug = cursor.fetchone()
        if not drug:
            conn.close()
            return jsonify({"success": False, "error": "藥物不存在"}), 404

        search_name = drug[0] or drug[1]
        if not search_name:
            conn.close()
            return jsonify({"success": False, "error": "藥物無名稱可搜尋"}), 400

        # 刪除舊快取
        conn.execute("DELETE FROM nhi_cache WHERE drug_id = ?", (drug_id,))
        conn.commit()
        conn.close()

        # 重新爬取
        import asyncio
        from nhi_crawler import scrape_nhi_drug_info

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(scrape_nhi_drug_info(search_name))

        if result and result.get("status") == "success":
            details = result.get("details", {})
            if details and len(details) > 2:
                from drug_database import DrugDatabase

                db = DrugDatabase(config.DATABASE_PATH)
                db.set_nhi_cache(drug_id, search_name, details)
                return jsonify(
                    {"success": True, "details": details, "message": "已重新爬取並快取"}
                )

        return jsonify(
            {"success": True, "details": {}, "message": "爬取完成但無額外資訊"}
        )
    except Exception as e:
        logger.error(f"✗ 重新爬取失敗: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# 上傳檔案管理 API
# ============================================


@admin_bp.route("/api/uploads", methods=["GET"])
def list_uploads():
    """列出所有上傳檔案"""
    try:
        from config import config

        uploads_path = Path(config.UPLOAD_FOLDER)
        files = []

        if uploads_path.exists():
            for f in sorted(
                uploads_path.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True
            ):
                if f.is_file():
                    stat = f.stat()
                    files.append(
                        {
                            "name": f.name,
                            "size_kb": round(stat.st_size / 1024, 1),
                            "modified": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "age_hours": round(
                                (datetime.now().timestamp() - stat.st_mtime) / 3600, 1
                            ),
                        }
                    )

        total_size = sum(f["size_kb"] for f in files)
        return jsonify(
            {
                "success": True,
                "files": files,
                "total": len(files),
                "total_size_mb": round(total_size / 1024, 2),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/uploads/<filename>", methods=["DELETE"])
def delete_upload(filename):
    """刪除指定上傳檔案"""
    try:
        from config import config

        filepath = Path(config.UPLOAD_FOLDER) / filename
        if ".." in filename or "/" in filename:
            return jsonify({"success": False, "error": "不安全的檔名"}), 400
        if filepath.exists():
            filepath.unlink()
            return jsonify({"success": True, "message": f"已刪除 {filename}"})
        return jsonify({"success": False, "error": "檔案不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/uploads/cleanup", methods=["POST"])
def cleanup_uploads():
    """清理舊的上傳檔案"""
    try:
        from config import config

        hours = request.get_json().get("hours", 24) if request.is_json else 24
        uploads_path = Path(config.UPLOAD_FOLDER)
        deleted = 0
        freed_kb = 0

        if uploads_path.exists():
            cutoff = datetime.now().timestamp() - (hours * 3600)
            for f in uploads_path.iterdir():
                if f.is_file() and f.stat().st_mtime < cutoff:
                    freed_kb += f.stat().st_size / 1024
                    f.unlink()
                    deleted += 1

        return jsonify(
            {
                "success": True,
                "deleted": deleted,
                "freed_mb": round(freed_kb / 1024, 2),
                "message": f"已清理 {deleted} 個檔案，釋放 {freed_kb/1024:.2f} MB",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# 系統設定 API
# ============================================


@admin_bp.route("/api/settings", methods=["GET"])
def get_settings():
    """取得目前系統設定"""
    try:
        from config import config

        return jsonify(
            {
                "success": True,
                "settings": {
                    "api_provider": config.API_PROVIDER,
                    "gemini_model": config.GEMINI_MODEL,
                    "min_confidence": config.MIN_CONFIDENCE,
                    "max_results": config.MAX_RESULTS,
                    "max_file_size_mb": config.MAX_FILE_SIZE / (1024 * 1024),
                    "allowed_extensions": list(config.ALLOWED_EXTENSIONS),
                    "cors_origins": config.CORS_ORIGINS,
                    "log_level": config.LOG_LEVEL,
                    "database_path": config.DATABASE_PATH,
                    "upload_folder": config.UPLOAD_FOLDER,
                    "flask_env": os.getenv("FLASK_ENV", "development"),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/logs", methods=["GET"])
def get_logs():
    """取得系統日誌（最近 100 行）"""
    try:
        log_file = Path(os.path.dirname(__file__)) / "app.log"
        if log_file.exists():
            lines = log_file.read_text(encoding="utf-8", errors="ignore").split("\n")
            return jsonify(
                {"success": True, "logs": lines[-100:], "total_lines": len(lines)}
            )
        return jsonify(
            {
                "success": True,
                "logs": ["(無日誌檔案，日誌輸出到 console)"],
                "total_lines": 0,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# API 使用統計
# ============================================


@admin_bp.route("/api/stats", methods=["GET"])
def api_stats():
    """取得 API 使用統計"""
    try:
        from config import config

        conn = get_db_connection(config.DATABASE_PATH)
        cursor = conn.cursor()

        stats = {"daily": [], "top_searches": [], "endpoints": [], "errors": 0}

        try:
            # 每日請求數（最近 7 天）
            cursor.execute("""
                SELECT date(created_at) as day, COUNT(*) as count
                FROM api_logs
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY day ORDER BY day
            """)
            stats["daily"] = [{"date": r[0], "count": r[1]} for r in cursor.fetchall()]

            # 熱門搜尋關鍵字
            cursor.execute("""
                SELECT query_params, COUNT(*) as count
                FROM api_logs
                WHERE endpoint LIKE '%search%' AND query_params IS NOT NULL AND query_params != ''
                GROUP BY query_params ORDER BY count DESC LIMIT 10
            """)
            stats["top_searches"] = [
                {"query": r[0], "count": r[1]} for r in cursor.fetchall()
            ]

            # 各端點使用次數
            cursor.execute("""
                SELECT endpoint, COUNT(*) as count, ROUND(AVG(duration_ms), 0) as avg_ms
                FROM api_logs
                GROUP BY endpoint ORDER BY count DESC
            """)
            stats["endpoints"] = [
                {"endpoint": r[0], "count": r[1], "avg_ms": r[2]}
                for r in cursor.fetchall()
            ]

            # 錯誤數
            cursor.execute("SELECT COUNT(*) FROM api_logs WHERE status_code >= 400")
            stats["errors"] = cursor.fetchone()[0]

        except sqlite3.OperationalError:
            pass

        conn.close()
        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================
# 批次更新 API
# ============================================


@admin_bp.route("/api/batch-update/start", methods=["POST"])
def batch_update_start():
    """啟動批次更新"""
    try:
        from config import config
        from batch_update import batch_job

        data = request.get_json() if request.is_json else {}
        delay = float(data.get("delay", 3.0))
        skip_cached = data.get("skip_cached", True)
        only_empty = data.get("only_empty", True)

        ok, msg = batch_job.start(
            db_path=config.DATABASE_PATH,
            delay=delay,
            skip_cached=skip_cached,
            only_empty=only_empty,
        )
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/batch-update/stop", methods=["POST"])
def batch_update_stop():
    """停止批次更新"""
    from batch_update import batch_job

    ok, msg = batch_job.stop()
    return jsonify({"success": ok, "message": msg})


@admin_bp.route("/api/batch-update/pause", methods=["POST"])
def batch_update_pause():
    """暫停批次更新"""
    from batch_update import batch_job

    ok, msg = batch_job.pause()
    return jsonify({"success": ok, "message": msg})


@admin_bp.route("/api/batch-update/resume", methods=["POST"])
def batch_update_resume():
    """繼續批次更新"""
    from batch_update import batch_job

    ok, msg = batch_job.resume()
    return jsonify({"success": ok, "message": msg})


@admin_bp.route("/api/batch-update/status", methods=["GET"])
def batch_update_status():
    """取得批次更新狀態"""
    from batch_update import batch_job

    return jsonify({"success": True, **batch_job.get_status()})
