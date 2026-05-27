"""
==============================================
SQLAlchemy ORM 模組 (models)
==============================================

【目的】
封裝既有 SQLite 資料表為 SQLAlchemy ORM Model，
讓後續 Auth / Medications / Safety 等新功能可以使用統一的 ORM 介面。

【向後相容】
- 既有 drug_database.py 的 raw sqlite3 邏輯保持不變
- 兩者共用同一個 .db 檔案（SQLAlchemy 與 sqlite3 並存）
- 後續會逐步遷移至 ORM

【使用方式】
    from models import db
    from models.drug import Drug

    drugs = Drug.query.filter(Drug.chinese_name.like("%普拿疼%")).limit(10).all()
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 匯出所有 Model 方便外部 import
from models.drug import Drug, DrugImage, NhiCache, ApiLog  # noqa: E402,F401
from models.user import User  # noqa: E402,F401
from models.profile import Profile  # noqa: E402,F401
from models.safety import (
    Ingredient,
    UserAllergy,
    SafetyCheckLog,
    drug_ingredients,
)  # noqa: E402,F401

__all__ = [
    "db",
    "Drug",
    "DrugImage",
    "NhiCache",
    "ApiLog",
    "User",
    "Profile",
    "Ingredient",
    "UserAllergy",
    "SafetyCheckLog",
    "drug_ingredients",
]
