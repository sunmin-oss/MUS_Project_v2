"""
Safety Blueprint（/api/safety）

S6-7：安全檢查 + 交互作用查詢 端點。
"""

import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db
from models.safety import DrugInteraction, Ingredient, UserAllergy
from services import SafetyCheckService

logger = logging.getLogger(__name__)

safety_bp = Blueprint("safety", __name__, url_prefix="/api/safety")


# ============================================
# S6-7  POST /api/safety/check
# ============================================


@safety_bp.route("/check", methods=["POST"])
@jwt_required()
def safety_check():
    """
    對指定藥物執行安全檢查。

    請求 JSON:
        {
            "drug_id": 123,
            "profile_id": 1    // 可選
        }

    回應:
        {
            "success": true,
            "overall": "safe|warning|danger",
            "checks": [ ... ]
        }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or not data.get("drug_id"):
        return jsonify({"success": False, "error": "drug_id 為必填"}), 400

    result = SafetyCheckService.check(
        user_id=user_id,
        drug_id=data["drug_id"],
        profile_id=data.get("profile_id"),
    )

    return jsonify({"success": True, **result}), 200


# ============================================
# S6-7  GET /api/safety/interactions
# ============================================


@safety_bp.route("/interactions", methods=["GET"])
@jwt_required()
def list_interactions():
    """
    查詢藥物交互作用（可依成分名稱搜尋）。

    Query params:
        ?ingredient=乙醯胺酚
        ?severity=severe
        ?page=1&per_page=20
    """
    ingredient_name = request.args.get("ingredient", "").strip()
    severity = request.args.get("severity", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    q = DrugInteraction.query

    if ingredient_name:
        # 搜尋包含該成分的交互
        ing = Ingredient.query.filter(
            Ingredient.name.like(f"%{ingredient_name}%")
        ).all()
        ing_ids = [i.id for i in ing]
        if ing_ids:
            q = q.filter(
                db.or_(
                    DrugInteraction.ingredient_a_id.in_(ing_ids),
                    DrugInteraction.ingredient_b_id.in_(ing_ids),
                )
            )
        else:
            return jsonify({"success": True, "interactions": [], "total": 0}), 200

    if severity:
        q = q.filter_by(severity=severity)

    total = q.count()
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    return (
        jsonify(
            {
                "success": True,
                "interactions": [i.to_dict() for i in items],
                "total": total,
                "page": page,
                "per_page": per_page,
            }
        ),
        200,
    )


# ============================================
# S6-3  User Allergies CRUD
# ============================================


@safety_bp.route("/allergies", methods=["GET"])
@jwt_required()
def list_allergies():
    user_id = int(get_jwt_identity())
    allergies = UserAllergy.query.filter_by(user_id=user_id).all()
    return (
        jsonify({"success": True, "allergies": [a.to_dict() for a in allergies]}),
        200,
    )


@safety_bp.route("/allergies", methods=["POST"])
@jwt_required()
def add_allergy():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True)
    if not data or not data.get("ingredient_id"):
        return jsonify({"success": False, "error": "ingredient_id 為必填"}), 400

    # 檢查成分存在
    ing = Ingredient.query.get(data["ingredient_id"])
    if not ing:
        return jsonify({"success": False, "error": "成分不存在"}), 404

    # 檢查重複
    existing = UserAllergy.query.filter_by(
        user_id=user_id, ingredient_id=ing.id
    ).first()
    if existing:
        return jsonify({"success": False, "error": "已記錄此過敏成分"}), 409

    severity = data.get("severity", "moderate")
    if severity not in ("mild", "moderate", "severe"):
        severity = "moderate"

    allergy = UserAllergy(
        user_id=user_id,
        ingredient_id=ing.id,
        severity=severity,
        note=data.get("note"),
    )
    db.session.add(allergy)
    db.session.commit()
    return jsonify({"success": True, "allergy": allergy.to_dict()}), 201


@safety_bp.route("/allergies/<int:allergy_id>", methods=["DELETE"])
@jwt_required()
def remove_allergy(allergy_id):
    user_id = int(get_jwt_identity())
    allergy = UserAllergy.query.filter_by(id=allergy_id, user_id=user_id).first()
    if not allergy:
        return jsonify({"success": False, "error": "紀錄不存在"}), 404
    db.session.delete(allergy)
    db.session.commit()
    return jsonify({"success": True, "message": "已刪除"}), 200
