"""
==============================================
藥物辨識系統 v2 - 配置檔案 (config.py)
==============================================

【功能說明】
管理系統的所有配置選項，包括 API 密鑰、上傳檔案限制等。

【環境變數】
- GOOGLE_VISION_API_KEY: Google Cloud Vision API 密鑰
- CLAUDE_API_KEY: Anthropic Claude API 密鑰（備選）
- API_PROVIDER: 使用的 API 提供商 ('google' 或 'claude')
- UPLOADFOLDER: 檔案上傳目錄
- MAX_FILE_SIZE: 最大上傳檔案大小（位元組）

【作者】MUS2 團隊
【日期】2025
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()


class Config:
    """應用配置基類"""

    # Flask 設定
    DEBUG = os.getenv("FLASK_DEBUG", False)
    TESTING = False

    # 檔案上傳設定
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}

    # API 設定
    API_PROVIDER = os.getenv("API_PROVIDER", "gemini")  # 'gemini', 'google' 或 'claude'

    # Google Gemini API (推薦)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = "gemini-2.5-flash"  # 使用目前可用且已驗證的 gemini-2.5-flash 模型

    # Google Vision API
    GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
    GOOGLE_VISION_API_URL = "https://vision.googleapis.com/v1/images:annotate"

    # Claude Vision API
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
    CLAUDE_MODEL = "claude-3-5-sonnet-20241022"

    # 藥物資料庫設定 (使用絕對路徑確保在任何目錄都能找到)
    _db_path = os.getenv("DATABASE_PATH")
    if _db_path:
        # 若 .env 設成相對路徑，相對於專案根目錄解析
        DATABASE_PATH = (
            _db_path
            if os.path.isabs(_db_path)
            else os.path.join(os.path.dirname(os.path.abspath(__file__)), _db_path)
        )
    else:
        # 預設使用 MUS2 目錄中的資料庫
        DATABASE_PATH = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "drug_recognition.db"
        )

    # SQLAlchemy 設定（P0-1）
    # 注意：Windows 路徑需轉為 forward-slash，否則 sqlite URI 會解析失敗
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{Path(DATABASE_PATH).as_posix()}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "connect_args": {"check_same_thread": False},
    }

    # JWT 設定（A1-3）
    _jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not _jwt_secret and os.getenv("FLASK_ENV") == "production":
        raise RuntimeError(
            "JWT_SECRET_KEY 未設定！Production 環境禁止使用隨機秘鑰，"
            "請在 .env 或環境變數中設定固定的 JWT_SECRET_KEY"
        )
    JWT_SECRET_KEY = _jwt_secret or os.urandom(32).hex()
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv("JWT_ACCESS_EXPIRES", 900))  # 15 分鐘
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv("JWT_REFRESH_EXPIRES", 604800))  # 7 天

    # CORS 設定
    CORS_ORIGINS = [
        "http://localhost:*",
        "http://127.0.0.1:*",
        "capacitor://localhost",
        "ionic://localhost",
        "http://localhost",
        "https://mus2.vercel.app",
        "https://*.vercel.app",
        "https://*.ngrok-free.dev",
    ]

    # 辨識設定
    MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", 0.3))  # 最低信心度閾值
    MAX_RESULTS = int(os.getenv("MAX_RESULTS", 5))  # 最多回傳結果數

    # 日誌設定
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def init_upload_folder(cls):
        """確保上傳資料夾存在"""
        Path(cls.UPLOAD_FOLDER).mkdir(exist_ok=True, parents=True)


class DevelopmentConfig(Config):
    """開發環境配置"""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """生產環境配置"""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """測試環境配置"""

    DEBUG = True
    TESTING = True
    DATABASE_PATH = ":memory:"


# 根據環境變數選擇配置
FLASK_ENV = os.getenv("FLASK_ENV", "development")

if FLASK_ENV == "production":
    config = ProductionConfig()
elif FLASK_ENV == "testing":
    config = TestingConfig()
else:
    config = DevelopmentConfig()
