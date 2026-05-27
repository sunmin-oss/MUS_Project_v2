"""
Auth Blueprint（/api/auth）

提供使用者註冊、登入、Token 刷新、登出、Profile CRUD 端點。
"""

import logging
from datetime import date

from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)

from models import db
from models.user import User
from models.profile import Profile

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# ── JWT Token 黑名單（登出用）──────────────
_token_blocklist: set[str] = set()


def is_token_revoked(jwt_header, jwt_payload) -> bool:
    """供 JWTManager.token_in_blocklist_loader 呼叫"""
    return jwt_payload["jti"] in _token_blocklist


# ============================================
# A1-2  註冊
# ============================================


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
    if not all(c.isalnum() or c in "_-" for c in username):
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


# ============================================
# A1-3  登入（取得 Access + Refresh Token）
# ============================================


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "缺少 JSON body"}), 400

    username = (data.get("username") or "").strip().lower()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"success": False, "error": "帳號與密碼為必填"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"success": False, "error": "帳號或密碼錯誤"}), 401

    if not user.is_active:
        return jsonify({"success": False, "error": "帳號已停用"}), 403

    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    logger.info(f"✓ 使用者登入: {username} (id={user.id})")
    return (
        jsonify(
            {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user": user.to_dict(),
            }
        ),
        200,
    )


# ============================================
# A1-3  刷新 Access Token
# ============================================


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    new_access = create_access_token(identity=identity)
    return jsonify({"success": True, "access_token": new_access}), 200


# ============================================
# A1-3  登出（撤銷 Token）
# ============================================


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    _token_blocklist.add(jti)
    logger.info(f"✓ Token 已撤銷: {jti[:8]}...")
    return jsonify({"success": True, "message": "已登出"}), 200


# ============================================
# A1-4  取得目前使用者
# ============================================


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"success": False, "error": "使用者不存在"}), 404
    return jsonify({"success": True, "user": user.to_dict()}), 200


# ============================================
# A1-8  Profile CRUD（家庭成員管理）
# ============================================


@auth_bp.route("/profiles", methods=["GET"])
@jwt_required()
def list_profiles():
    user_id = int(get_jwt_identity())
    profiles = (
        Profile.query.filter_by(user_id=user_id)
        .order_by(Profile.is_default.desc())
        .all()
    )
    return jsonify({"success": True, "profiles": [p.to_dict() for p in profiles]}), 200


@auth_bp.route("/profiles", methods=["POST"])
@jwt_required()
def create_profile():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or not (data.get("name") or "").strip():
        return jsonify({"success": False, "error": "name 為必填"}), 400

    # 若為第一個 profile，自動設為預設
    existing_count = Profile.query.filter_by(user_id=user_id).count()

    birth = None
    if data.get("birth_date"):
        try:
            birth = date.fromisoformat(data["birth_date"])
        except ValueError:
            return (
                jsonify({"success": False, "error": "birth_date 格式須為 YYYY-MM-DD"}),
                400,
            )

    profile = Profile(
        user_id=user_id,
        name=data["name"].strip(),
        relationship=data.get("relationship"),
        birth_date=birth,
        allergies=data.get("allergies"),
        note=data.get("note"),
        is_default=(existing_count == 0),
    )
    db.session.add(profile)
    db.session.commit()
    return jsonify({"success": True, "profile": profile.to_dict()}), 201


@auth_bp.route("/profiles/<int:profile_id>", methods=["PUT"])
@jwt_required()
def update_profile(profile_id):
    user_id = int(get_jwt_identity())
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first()
    if not profile:
        return jsonify({"success": False, "error": "Profile 不存在"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return jsonify({"success": False, "error": "name 不可為空"}), 400
        profile.name = name
    if "relationship" in data:
        profile.relationship = data["relationship"]
    if "birth_date" in data:
        if data["birth_date"]:
            try:
                profile.birth_date = date.fromisoformat(data["birth_date"])
            except ValueError:
                return (
                    jsonify(
                        {"success": False, "error": "birth_date 格式須為 YYYY-MM-DD"}
                    ),
                    400,
                )
        else:
            profile.birth_date = None
    if "allergies" in data:
        profile.allergies = data["allergies"]
    if "note" in data:
        profile.note = data["note"]
    if "is_default" in data and data["is_default"]:
        # 取消其他 default
        Profile.query.filter(
            Profile.user_id == user_id, Profile.id != profile_id
        ).update({"is_default": False})
        profile.is_default = True

    db.session.commit()
    return jsonify({"success": True, "profile": profile.to_dict()}), 200


@auth_bp.route("/profiles/<int:profile_id>", methods=["DELETE"])
@jwt_required()
def delete_profile(profile_id):
    user_id = int(get_jwt_identity())
    profile = Profile.query.filter_by(id=profile_id, user_id=user_id).first()
    if not profile:
        return jsonify({"success": False, "error": "Profile 不存在"}), 404

    db.session.delete(profile)
    db.session.commit()
    return jsonify({"success": True, "message": "Profile 已刪除"}), 200
