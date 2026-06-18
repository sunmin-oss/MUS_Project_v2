"""
==============================================
藥物辨識系統 v2 - 主程式 (main.py)
==============================================

【專題說明】
這是一個簡化版的藥物辨識系統，改用 Google Vision API 進行藥物辨識，
設計師視野友好的介面，適合年長者使用。

【檔案功能】
Flask 後端主程式，提供簡化 RESTful API 介面。
主要功能:
1. 接收前端上傳的藥物圖片
2. 呼叫 Google Vision API 識別藥物內容
3. 查詢本地資料庫取得詳細藥物資訊
4. 支援簡單的藥物名稱搜尋

【API 端點】
- GET  /api/health              - 檢查系統狀態
- POST /api/recognize           - 上傳圖片進行藥物辨識
- POST /api/search              - 按名稱搜尋藥物
- GET  /api/drug/<id>           - 取得藥物詳細資訊
- GET  /api/images/<filename>   - 取得藥物圖片

【技術棧】
- Flask: Python Web 框架
- Google Vision API: 影像識別
- SQLite: 藥物資料庫
- Claude API: 備選智能識別

【作者】MUS2 團隊
【日期】2025
"""

from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
import os
import uuid
import logging
import sqlite3
import time
from datetime import datetime
from typing import Dict, Any, Tuple
import sys

# 載入配置
from config import config

# 設定日誌
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 初始化 Flask 應用
app = Flask(__name__)
app.config.from_object(config)

# 初始化上傳資料夾
config.init_upload_folder()

# 初始化 SQLAlchemy ORM（P0-1）
from models import db

db.init_app(app)

# 初始化 JWT（A1-3）
from flask_jwt_extended import JWTManager
from datetime import timedelta

app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    seconds=config.JWT_ACCESS_TOKEN_EXPIRES
)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(
    seconds=config.JWT_REFRESH_TOKEN_EXPIRES
)
jwt = JWTManager(app)

# JWT Token 黑名單檢查（A1-3）
from routes.auth import is_token_revoked

jwt.token_in_blocklist_loader(is_token_revoked)

# 初始化 Rate Limiter（P0-5）
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute"],
    storage_uri="memory://",
)

# 配置 CORS
CORS(
    app,
    resources={
        "/api/*": {"origins": config.CORS_ORIGINS},
        "/admin/*": {"origins": config.CORS_ORIGINS},
    },
)

# 註冊 Blueprints（P0-3）
from admin_routes import admin_bp
from routes import auth_bp, medications_bp, safety_bp

app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(medications_bp)
app.register_blueprint(safety_bp)

# 建立新增資料表（users 等，不影響既有表）
with app.app_context():
    db.create_all()

# 確保既有資料庫有 is_admin 欄位（向下相容）
from admin_routes import _ensure_admin_column

with app.app_context():
    _ensure_admin_column()

# 初始化排程器（S1-3：非測試模式才啟動）
if not app.config.get("TESTING"):
    from services.scheduler import init_scheduler

    init_scheduler(app)


# ============================================
# API 使用追蹤（背景批次寫入，避免 SQLite writer lock）
# ============================================

import threading
import queue as _queue

_log_queue: _queue.Queue = _queue.Queue()
_LOG_FLUSH_INTERVAL = 2  # 秒
_LOG_BATCH_SIZE = 50


def _ensure_api_logs_table():
    """確保 api_logs 表存在"""
    try:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                method TEXT,
                status_code INTEGER,
                duration_ms REAL,
                query_params TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"⚠ 建立 api_logs 表失敗: {e}")


def _log_writer_loop():
    """背景 thread：批次寫入 api_logs + 定期清理 30 天前紀錄"""
    cleanup_counter = 0
    while True:
        batch = []
        try:
            # 等待第一筆，最多等 _LOG_FLUSH_INTERVAL 秒
            item = _log_queue.get(timeout=_LOG_FLUSH_INTERVAL)
            batch.append(item)
        except _queue.Empty:
            pass

        # 取出隊列中剩餘項目（最多 _LOG_BATCH_SIZE）
        while len(batch) < _LOG_BATCH_SIZE:
            try:
                batch.append(_log_queue.get_nowait())
            except _queue.Empty:
                break

        if batch:
            try:
                conn = sqlite3.connect(config.DATABASE_PATH)
                conn.executemany(
                    "INSERT INTO api_logs (endpoint, method, status_code, duration_ms, query_params, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    batch,
                )
                conn.commit()
                conn.close()
            except Exception:
                pass  # 日誌寫入失敗不應影響系統

        # 每 ~500 次 flush（約 15-30 分鐘）清理舊紀錄
        cleanup_counter += 1
        if cleanup_counter >= 500:
            cleanup_counter = 0
            try:
                conn = sqlite3.connect(config.DATABASE_PATH)
                conn.execute(
                    "DELETE FROM api_logs WHERE created_at < datetime('now', '-30 days')"
                )
                conn.commit()
                conn.close()
            except Exception:
                pass


_ensure_api_logs_table()

# 啟動背景寫入 thread（daemon=True 隨主程序退出）
_writer_thread = threading.Thread(target=_log_writer_loop, daemon=True)
_writer_thread.start()


@app.before_request
def before_request_timer():
    """記錄請求開始時間"""
    g.start_time = time.time()


@app.after_request
def log_api_request(response):
    """記錄 API 請求（放入背景佇列，批次寫入）"""
    path = request.path
    if not path.startswith("/api/") or path.startswith("/api/images/"):
        return response

    try:
        duration_ms = (time.time() - getattr(g, "start_time", time.time())) * 1000
        query_params = ""
        if "search" in path:
            data = request.get_json(silent=True)
            if data and data.get("query"):
                query_params = data["query"]

        _log_queue.put_nowait(
            (
                path,
                request.method,
                response.status_code,
                round(duration_ms, 1),
                query_params,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
    except _queue.Full:
        pass  # 佇列滿時丟棄，不影響請求

    return response


# 禁用前端文件的緩存
@app.after_request
def disable_cache(response):
    """禁用前端文件的緩存，確保每次都加載最新版本"""
    request_path = request.path
    if request_path and (
        request_path.endswith(".html")
        or request_path.endswith(".js")
        or request_path.endswith(".css")
        or request_path == "/"
    ):
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# 動態匯入 API 提供商
try:
    if config.API_PROVIDER.lower() == "gemini":
        from vision_api_gemini import GeminiVisionRecognizer

        recognizer = GeminiVisionRecognizer(config.GEMINI_API_KEY, config.GEMINI_MODEL)
        logger.info("✓ Google Gemini Vision API 已初始化")
    elif config.API_PROVIDER.lower() == "google":
        from vision_api_google import GoogleVisionRecognizer

        recognizer = GoogleVisionRecognizer(config.GOOGLE_VISION_API_KEY)
        logger.info("✓ Google Vision API 已初始化")
    elif config.API_PROVIDER.lower() == "claude":
        from vision_api_claude import ClaudeVisionRecognizer

        recognizer = ClaudeVisionRecognizer(config.CLAUDE_API_KEY)
        logger.info("✓ Claude Vision API 已初始化")
    else:
        raise ValueError(f"未知的 API 提供商: {config.API_PROVIDER}")
except Exception as e:
    logger.error(f"✗ 無法初始化視覺 API: {e}")
    recognizer = None

# 動態匯入資料庫模組
try:
    from drug_database import DrugDatabase

    drug_db = DrugDatabase(config.DATABASE_PATH)
    logger.info(f"✓ 藥物資料庫已載入 ({config.DATABASE_PATH})")
except Exception as e:
    logger.warning(f"⚠ 藥物資料庫初始化失敗: {e}")
    drug_db = None


def allowed_file(filename: str) -> bool:
    """檢查檔案是否被允許上傳"""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS
    )


def get_file_size_mb(file) -> float:
    """取得檔案大小（MB）"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size / (1024 * 1024)


# ============================================
# 前端路由
# ============================================


@app.route("/", methods=["GET"])
def index():
    """提供前端主頁"""
    try:
        return send_from_directory(os.path.dirname(__file__), "index.html")
    except FileNotFoundError:
        logger.error("✗ index.html 檔案不存在")
        return jsonify({"success": False, "error": "前端檔案不存在"}), 500


# ============================================
# API 端點
# ============================================


@app.route("/api/health", methods=["GET"])
def health_check():
    """檢查系統狀態"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "vision_api": "ready" if recognizer else "unavailable",
            "database": "ready" if drug_db else "unavailable",
        },
    }

    if recognizer is None or drug_db is None:
        status["status"] = "degraded"
        return jsonify(status), 503

    return jsonify(status), 200


@app.route("/api/recognize", methods=["POST"])
@limiter.limit("30 per minute")
def recognize_drug():
    """
    藥物辨識端點

    請求:
        - 檔案: image (multipart/form-data)
        - 可選: language ('zh' for 中文, 'en' for English)
        - 可選: Authorization: Bearer <token>（記錄辨識歷史）

    回應:
        {
            "success": true,
            "request_id": "uuid",
            "recognized_items": [
                {
                    "name": "藥物名稱",
                    "confidence": 0.95,
                    "drug_id": 123,
                    "details": {...}
                },
                ...
            ],
            "message": "辨識完成"
        }
    """
    try:
        # 驗證請求
        if recognizer is None:
            return jsonify({"success": False, "error": "視覺 API 暫不可用"}), 503

        if "image" not in request.files:
            return jsonify({"success": False, "error": "未找到圖片檔案"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "檔案名稱為空"}), 400

        # 檢查檔案類型
        if not allowed_file(file.filename):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f'不支持的檔案格式。允許格式: {", ".join(config.ALLOWED_EXTENSIONS)}',
                    }
                ),
                400,
            )

        # 檢查檔案大小
        file_size_mb = get_file_size_mb(file)
        if file_size_mb > (config.MAX_FILE_SIZE / (1024 * 1024)):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"檔案太大 ({file_size_mb:.1f}MB)，限制: {config.MAX_FILE_SIZE/(1024*1024):.1f}MB",
                    }
                ),
                413,
            )

        # 儲存上傳的檔案（加入模式前綴以區分辨識類型）
        filename = "drug_" + str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.info(f"✓ 檔案已儲存: {filepath}")

        # 調用 Vision API 進行辨識 (優先使用 RAG 模式)
        try:
            # 嘗試使用 RAG 模式（如果有資料庫且 recognizer 支持）
            if (
                drug_db
                and hasattr(recognizer, "recognize_with_rag")
                and callable(getattr(recognizer, "recognize_with_rag"))
            ):
                logger.info("📚 使用 RAG 模式識別...")
                recognition_results = recognizer.recognize_with_rag(filepath, drug_db)
            else:
                logger.info("🔍 使用普通模式識別...")
                recognition_results = recognizer.recognize(filepath)
        except Exception as e:
            logger.error(f"✗ 辨識失敗: {e}")
            return jsonify({"success": False, "error": f"辨識失敗: {str(e)}"}), 500

        if not recognition_results:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "未能識別出藥物，請嘗試拍攝更清晰的照片",
                    }
                ),
                200,
            )

        # 查詢資料庫以獲取詳細資訊
        recognized_items = []
        language = request.form.get("language", "zh")

        for item in recognition_results[: config.MAX_RESULTS]:
            drug_name = item.get("name", "")
            confidence = item.get("confidence", 0)
            source = item.get("source", "unknown")

            # 過濾信心度低的結果
            if confidence < config.MIN_CONFIDENCE:
                continue

            drug_detail = None

            # 如果是 RAG 模式，直接使用 drug_id 查詢
            if source == "gemini_rag" and item.get("drug_id"):
                if drug_db:
                    try:
                        drug_detail = drug_db.get_drug_by_id(item.get("drug_id"))
                    except Exception as e:
                        logger.warning(f"⚠ 查詢藥物 ID {item.get('drug_id')} 失敗: {e}")
            # 否則按名稱查詢
            else:
                if drug_db:
                    try:
                        drug_detail_list = drug_db.search_by_name(drug_name, limit=1)
                        if drug_detail_list:
                            drug_detail = drug_detail_list[0]
                    except Exception as e:
                        logger.warning(f"⚠ 查詢藥物 {drug_name} 失敗: {e}")

            # 取得藥物圖片
            images = []
            drug_id = drug_detail.get("id") if drug_detail else item.get("drug_id")
            if drug_db and drug_id:
                try:
                    images = drug_db.get_drug_images(drug_id, limit=3)
                except Exception as e:
                    logger.warning(f"⚠ 取得圖片失敗 (drug_id={drug_id}): {e}")

            recognized_items.append(
                {
                    "name": drug_name,
                    "confidence": round(confidence, 3),
                    "drug_id": drug_id,
                    "source": source,
                    "reason": item.get("reason", ""),
                    "images": images,
                    "details": (
                        {
                            "chinese_name": (
                                drug_detail.get("chinese_name", drug_name)
                                if drug_detail
                                else None
                            ),
                            "english_name": (
                                drug_detail.get("english_name") if drug_detail else None
                            ),
                            "license_number": (
                                drug_detail.get("license_number")
                                if drug_detail
                                else None
                            ),
                            "shape": drug_detail.get("shape") if drug_detail else None,
                            "color": drug_detail.get("color") if drug_detail else None,
                            "usage": drug_detail.get("usage") if drug_detail else None,
                        }
                        if drug_detail
                        else None
                    ),
                }
            )

        response = {
            "success": True,
            "request_id": filename.split("_")[0],
            "recognized_items": recognized_items,
            "message": f"辨識完成，找到 {len(recognized_items)} 個匹配結果",
        }

        # S6-8: 若有 JWT token 則自動執行安全檢查
        safety_warnings = []
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

            verify_jwt_in_request(optional=True)
            uid = get_jwt_identity()
            if uid:
                from services import SafetyCheckService

                for item in recognized_items:
                    did = item.get("drug_id")
                    if did:
                        result = SafetyCheckService.check(user_id=int(uid), drug_id=did)
                        if result["overall"] != "safe":
                            safety_warnings.append(
                                {"drug_id": did, "name": item["name"], **result}
                            )
        except Exception:
            pass  # JWT 驗證失敗或無 token 時靜默略過

        if safety_warnings:
            response["safety_warnings"] = safety_warnings

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"✗ API 錯誤: {e}", exc_info=True)
        return jsonify({"success": False, "error": "伺服器內部錯誤"}), 500


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/debug_prescription", methods=["POST"])
def debug_prescription():
    """臨時 debug endpoint，測試藥單 OCR 並回傳 Gemini 原始回應"""
    try:
        if recognizer is None or not hasattr(recognizer, "recognize_prescription"):
            return jsonify({"error": "recognizer 不支持 prescription"}), 503

        if "image" not in request.files:
            return jsonify({"error": "no image"}), 400

        file = request.files["image"]
        filename = "debug_" + str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        # 直接呼叫 Gemini API 並取得原始回應
        import base64
        from pathlib import Path

        image_file = Path(filepath)
        with open(image_file, "rb") as f:
            image_data = f.read()

        suffix = image_file.suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}
        mime_type = mime_map.get(suffix, "image/jpeg")
        image_b64 = base64.standard_b64encode(image_data).decode("utf-8")

        import requests as req_lib
        api_url = f"{recognizer.base_url}/{recognizer.model_name}:generateContent?key={recognizer.api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": "請分析這張藥單照片，提取藥物名稱，回傳 JSON 陣列 [{\"chinese_name\":\"...\"}]。只回傳 JSON。"},
                    {"inline_data": {"mime_type": mime_type, "data": image_b64}}
                ]
            }]
        }
        response = req_lib.post(api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)

        # 清理暫存
        os.remove(filepath)

        result = {
            "gemini_status": response.status_code,
            "gemini_response_keys": list(response.json().keys()) if response.status_code == 200 else None,
        }

        if response.status_code == 200:
            data = response.json()
            if "candidates" in data and data["candidates"]:
                parts = data["candidates"][0].get("content", {}).get("parts", [])
                result["parts_count"] = len(parts)
                result["parts_info"] = [
                    {"has_thought": part.get("thought", False), "text_preview": part.get("text", "")[:200]}
                    for part in parts
                ]
            else:
                result["raw_response_preview"] = str(response.json())[:500]
        else:
            result["error_response"] = response.text[:500]

        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/recognize_prescription", methods=["POST"])
def recognize_prescription():
    """
    藥單辨識端點

    請求:
        - 檔案: image (multipart/form-data)

    回應:
        {
            "success": true,
            "request_id": "uuid",
            "recognized_drugs": ["普拿疼", "Amoxicillin"],
            "drug_details": [
                {
                    "name": "普拿疼",
                    ...詳細資訊
                }
            ],
            "message": "辨識完成"
        }
    """
    try:
        if recognizer is None or not hasattr(recognizer, "recognize_prescription"):
            return (
                jsonify({"success": False, "error": "視覺 API 暫不支持藥單辨識"}),
                503,
            )

        if "image" not in request.files:
            return jsonify({"success": False, "error": "未找到圖片檔案"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "檔案名稱為空"}), 400

        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "不支持的檔案格式"}), 400

        file_size_mb = get_file_size_mb(file)
        if file_size_mb > (config.MAX_FILE_SIZE / (1024 * 1024)):
            return jsonify({"success": False, "error": "檔案太大"}), 413

        # 儲存上傳的檔案（加入模式前綴以區分辨識類型）
        filename = (
            "prescription_" + str(uuid.uuid4()) + "_" + secure_filename(file.filename)
        )
        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        file.save(filepath)
        logger.info(f"✓ 藥單圖片已儲存: {filepath}")

        # OCR 辨識
        try:
            logger.info("📄 開始進行藥單 OCR 辨識...")
            drug_names = recognizer.recognize_prescription(filepath)
        except Exception as e:
            logger.error(f"✗ 藥單辨識失敗: {e}")
            return jsonify({"success": False, "error": f"辨識失敗: {str(e)}"}), 500

        if not drug_names:
            return (
                jsonify({"success": False, "error": "未能從藥單中識別出任何藥物"}),
                200,
            )

        # 將名稱轉化並收集 DB 資料 (為了前端簡單顯示)
        drug_details = []

        # 取得 Gemini 結構化資料（含許可證字號）
        # 優先使用 _last_prescription_details (side-channel)
        # 若為空則嘗試直接從 recognizer 的內部狀態取得
        prescription_details = (
            getattr(recognizer, "_last_prescription_details", None) or []
        )
        logger.info(f"📄 OCR 結果: {len(drug_names)} 個藥名, {len(prescription_details)} 筆結構化資料")
        if prescription_details:
            logger.info(f"📄 結構化資料範例: {json.dumps(prescription_details[0], ensure_ascii=False)[:200]}")
        else:
            logger.warning(f"⚠ prescription_details 為空！")

        for idx, name in enumerate(drug_names):
            detail = {
                "name": name,
                "confidence": 1.0,
                "source": "prescription",
                "details": None,
                "drug_id": None,
                "prescription_info": None,
            }

            # 附加處方資訊（用法用量）— 用 index 對齊
            if idx < len(prescription_details):
                item = prescription_details[idx]
                detail["prescription_info"] = {
                    "route": item.get("route", ""),
                    "days": item.get("days", 0),
                    "frequency": item.get("frequency", ""),
                    "dose_per_time": item.get("dose_per_time", ""),
                    "total_quantity": item.get("total_quantity", ""),
                    "ingredient": item.get("ingredient", ""),
                }
            else:
                logger.warning(f"⚠ idx={idx} 超出 prescription_details 長度 {len(prescription_details)}")

            if drug_db:
                try:
                    db_drug = None

                    # 優先用許可證字號精確比對
                    if idx < len(prescription_details):
                        item = prescription_details[idx]
                        lic = item.get("license_number", "")
                        if lic:
                            results = drug_db.search_by_name(lic, limit=1)
                            if results:
                                db_drug = results[0]

                    # 許可證字號找不到，用中文名搜尋
                    if not db_drug:
                        results = drug_db.search_by_name(name, limit=1)
                        if results:
                            db_drug = results[0]

                    # 中文名也找不到，嘗試英文名
                    if not db_drug and idx < len(prescription_details):
                        en_name = prescription_details[idx].get("english_name", "")
                        if en_name:
                            results = drug_db.search_by_name(en_name, limit=1)
                            if results:
                                db_drug = results[0]

                    if db_drug:
                        detail["drug_id"] = db_drug.get("id")
                        detail["details"] = {
                            "chinese_name": db_drug.get("chinese_name"),
                            "english_name": db_drug.get("english_name"),
                            "license_number": db_drug.get("license_number"),
                            "shape": db_drug.get("shape"),
                            "color": db_drug.get("color"),
                            "indications": db_drug.get("indications"),
                        }

                        # Add image if exists
                        try:
                            images = drug_db.get_drug_images(detail["drug_id"], limit=1)
                            detail["images"] = images
                        except:
                            detail["images"] = []
                except Exception as e:
                    logger.warning(f"⚠ 查詢藥單藥物 {name} 失敗: {e}")

            drug_details.append(detail)

        response = {
            "success": True,
            "request_id": filename.split("_")[0],
            "image_filename": filename,
            "recognized_drugs": drug_names,
            "recognized_items": drug_details,  # 保持與 recognize_drug 一致的格式
            "message": f"辨識完成，找到 {len(drug_names)} 種藥物",
        }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"✗ API 錯誤: {e}", exc_info=True)
        return jsonify({"success": False, "error": "伺服器內部錯誤"}), 500


@app.route("/api/search", methods=["POST"])
def search_drug():
    """
    藥物名稱搜尋端點（優先使用資料庫，若無結果則使用 Gemini AI 搜尋）

    請求:
        {
            "query": "普拿疼",
            "limit": 5
        }

    回應:
        {
            "success": true,
            "results": [...],
            "total": 10,
            "source": "database" 或 "gemini"
        }
    """
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        limit = min(int(data.get("limit", 10)), 20)

        if not query or len(query) < 2:
            return jsonify({"success": False, "error": "搜尋關鍵字至少 2 個字符"}), 400

        results = []
        source = None

        # 1. 優先使用數據庫搜尋
        if drug_db:
            logger.info(f"📚 使用數據庫搜尋: {query}")
            results = drug_db.search_by_name(query, limit=limit)
            if results:
                source = "database"
                logger.info(f"✓ 資料庫搜尋找到 {len(results)} 筆結果")
                # 為每筆結果附上圖片資訊
                for r in results:
                    drug_id = r.get("drug_id") or r.get("id")
                    if drug_id:
                        r["images"] = drug_db.get_drug_images(drug_id, limit=3)
                return (
                    jsonify(
                        {
                            "success": True,
                            "results": results,
                            "total": len(results),
                            "source": source,
                        }
                    ),
                    200,
                )

        # 2. 資料庫搜尋無結果，使用 Gemini AI 搜尋
        logger.info(f"🤖 資料庫搜尋無結果，改用 Gemini 搜尋: {query}")

        if recognizer:
            try:
                results = recognizer.search_by_text(query, limit=limit)
                if results:
                    source = "gemini"
                    logger.info(f"✓ Gemini 搜尋找到 {len(results)} 筆結果")
                    return (
                        jsonify(
                            {
                                "success": True,
                                "results": results,
                                "total": len(results),
                                "source": source,
                            }
                        ),
                        200,
                    )
            except Exception as e:
                logger.warning(f"⚠️ Gemini 搜尋失敗: {e}")

        # 3. 如果上述方法都無結果
        logger.warning(f"⚠️ 無法找到搜尋結果: {query}")
        return (
            jsonify(
                {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "message": "未找到相關藥物。請稍微更改搜尋條件或使用拍照辨識功能。",
                }
            ),
            200,
        )

    except ValueError:
        logger.error(f"❌ 搜尋請求格式錯誤")
        return jsonify({"success": False, "error": "搜尋請求格式錯誤"}), 400
    except Exception as e:
        logger.error(f"✗ 搜尋錯誤: {e}", exc_info=True)
        return jsonify({"success": False, "error": "搜尋失敗，請重試"}), 500


@app.route("/api/drug/<drug_id>", methods=["GET"])
def get_drug_detail(drug_id):
    """取得單一藥物詳細資訊"""
    try:
        if not drug_db:
            return jsonify({"success": False, "error": "資料庫暫不可用"}), 503

        drug = drug_db.get_drug_by_id(int(drug_id))

        if not drug:
            return jsonify({"success": False, "error": "藥物不存在"}), 404

        # 取得藥物圖片
        try:
            images = drug_db.get_drug_images(int(drug_id), limit=5)
            drug["images"] = images
        except Exception as e:
            logger.warning(f"⚠ 取得藥物圖片失敗: {e}")
            drug["images"] = []

        # 整合 NHI 爬蟲取得最新副作用與適應症資訊（含快取機制）
        try:
            # 決定搜尋關鍵字 (優先使用中文品名，較精確；備選使用完整英文名)
            search_name = ""
            if drug.get("chinese_name"):
                search_name = drug.get("chinese_name")
            elif drug.get("english_name"):
                search_name = drug.get("english_name")

            if search_name and drug_db:
                # 1. 先查快取（7 天內有效）
                cached = drug_db.get_nhi_cache(int(drug_id))
                if cached:
                    drug["nhi_details"] = cached
                    logger.info(f"⚡ 使用 NHI 快取資料 (drug_id={drug_id})")
                else:
                    # 2. 快取未命中，啟動爬蟲
                    logger.info(f"🕸️ 快取未命中，從 NHI/TFDA 爬取: {search_name}")
                    import asyncio
                    from nhi_crawler import scrape_nhi_drug_info

                    try:
                        loop = asyncio.get_event_loop()
                    except RuntimeError:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                    nhi_result = loop.run_until_complete(
                        scrape_nhi_drug_info(search_name)
                    )

                    if nhi_result and nhi_result.get("status") == "success":
                        details = nhi_result.get("details", {})
                        if (
                            details and len(details) > 2
                        ):  # 至少有 id + source_url 以外的欄位
                            drug["nhi_details"] = details
                            # 3. 存入快取
                            drug_db.set_nhi_cache(int(drug_id), search_name, details)
                            logger.info("✓ NHI/TFDA 資訊已爬取並快取")
                        else:
                            logger.info("ℹ NHI/TFDA 無額外資訊可快取")
        except Exception as e:
            logger.warning(f"⚠ NHI 資訊擷取失敗: {e}")

        return jsonify({"success": True, "drug": drug}), 200

    except Exception as e:
        logger.error(f"✗ 詳細查詢錯誤: {e}")
        return jsonify({"success": False, "error": "查詢失敗"}), 500


@app.route("/api/prescription-image/<filename>", methods=["DELETE"])
def delete_prescription_image(filename):
    """刪除處方箋圖片"""
    try:
        # 驗證檔名安全性
        if ".." in filename or "/" in filename or "\\" in filename:
            return jsonify({"success": False, "error": "不安全的檔名"}), 400

        # 只允許刪除 prescription_ 開頭的檔案
        if not filename.startswith("prescription_"):
            return jsonify({"success": False, "error": "只能刪除處方箋圖片"}), 400

        filepath = os.path.join(config.UPLOAD_FOLDER, filename)
        if os.path.exists(filepath) and os.path.isfile(filepath):
            os.remove(filepath)
            logger.info(f"✓ 已刪除處方箋圖片: {filename}")
            return jsonify({"success": True, "message": "圖片已刪除"}), 200
        else:
            return jsonify({"success": True, "message": "圖片不存在，無需刪除"}), 200

    except Exception as e:
        logger.error(f"✗ 刪除處方箋圖片失敗: {e}")
        return jsonify({"success": False, "error": "刪除失敗"}), 500


@app.route("/api/images/<path:filepath>", methods=["GET"])
def get_image(filepath):
    """取得藥物圖片 (支援 medicine_photos 和 uploads 目錄)"""
    try:
        # 移除路徑開頭的 medicine_photos/ 如果有的話
        if filepath.startswith("medicine_photos/"):
            filepath = filepath[16:]  # 移除 "medicine_photos/" 前綴

        # 驗證路徑安全性 (不允許目錄遍歷)
        if ".." in filepath or filepath.startswith("/"):
            logger.warning(f"⚠ 不安全的路徑請求: {filepath}")
            return jsonify({"success": False, "error": "不安全的路徑"}), 400

        # 首先嘗試從 medicine_photos 目錄取得
        medicine_photos_path = os.path.join(
            os.path.dirname(__file__), "medicine_photos"
        )
        full_path = os.path.join(medicine_photos_path, filepath)

        logger.debug(f"🔍 嘗試讀取圖片: {full_path}")

        if os.path.exists(full_path) and os.path.isfile(full_path):
            return send_from_directory(medicine_photos_path, filepath)

        # 如果不在 medicine_photos，嘗試 uploads 目錄
        return send_from_directory(config.UPLOAD_FOLDER, filepath)

    except Exception as e:
        logger.warning(f"⚠ 圖片請求錯誤: {filepath} -> {e}")
        return jsonify({"success": False, "error": "圖片不存在"}), 404


# ============================================
# 錯誤處理
# ============================================


@app.errorhandler(404)
def not_found(error):
    """404 錯誤處理"""
    return jsonify({"success": False, "error": "端點不存在"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """405 錯誤處理"""
    return jsonify({"success": False, "error": "不允許的 HTTP 方法"}), 405


@app.errorhandler(429)
def ratelimit_handler(error):
    """429 Rate Limit 錯誤（P0-5）"""
    return jsonify({"success": False, "error": "請求過於頻繁，請稍後再試"}), 429


@app.errorhandler(500)
def internal_error(error):
    """500 錯誤處理"""
    logger.error(f"✗ 內部伺服器錯誤: {error}")
    return jsonify({"success": False, "error": "伺服器內部錯誤"}), 500


# ============================================
# 應用啟動
# ============================================

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("🚀 藥物辨識系統 v2 啟動")
    logger.info(f"📍 環境: {config.__class__.__name__}")
    logger.info(f"🔌 API 提供商: {config.API_PROVIDER}")
    logger.info(f"💾 資料庫: {config.DATABASE_PATH}")
    logger.info("=" * 50)

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=config.DEBUG)
