"""
Auth Blueprint（/api/auth）

提供使用者註冊、登入等認證端點。
"""

import logging

from flask import Blueprint, request, jsonify

from models import db
from models.user import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    使用者註冊

    請求 JSON:
        {
            "username": "alice",
            "password": "StrongP@ss1",
            "display_name": "小明"   # 可選
        }

    回應:
        201  {"success": true, "user_id": 1, "message": "註冊成功"}
        400  {"success": false, "error": "..."}
        409  {"success": false, "error": "使用者名稱已被使用"}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "缺少 JSON body"}), 400

    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or "").strip()

    # 驗證
    if not username or len(username) < 3:
        return jsonify({"success": False, "error": "使用者名稱至少 3 個字元"}), 400
    if len(username) > 32:
        return jsonify({"success": False, "error": "使用者名稱最多 32 個字元"}), 400
    if not username.isalnum() and not all(c.isalnum() or c in "_-" for c in username):
        return (
            jsonify(
                {"success": False, "error": "使用者名稱只能包含英數字、底線、連字號"}
            ),
            400,
        )
    if len(password) < 8:
        return jsonify({"success": False, "error": "密碼至少 8 個字元"}), 400

    # 檢查是否已存在
    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({"success": False, "error": "使用者名稱已被使用"}), 409

    user = User(username=username, display_name=display_name or username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    logger.info(f"✓ 新使用者註冊: {username} (id={user.id})")
    return jsonify({"success": True, "user_id": user.id, "message": "註冊成功"}), 201
