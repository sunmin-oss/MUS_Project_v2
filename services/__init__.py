"""
SafetyCheckService（S6-6）

四層安全檢查：過敏 → 重複用藥 → 交互作用 → 分級
"""

import logging
from typing import Optional

from models import db
from models.safety import (
    Ingredient,
    DrugInteraction,
    UserAllergy,
    SafetyCheckLog,
    drug_ingredients,
)
from models.medication import Medication
from models.drug import Drug

logger = logging.getLogger(__name__)


class SafetyCheckService:
    """用藥安全檢查服務"""

    @staticmethod
    def check(user_id: int, drug_id: int, profile_id: Optional[int] = None) -> dict:
        """
        對指定藥物執行四層安全檢查。

        回傳:
            {
                "overall": "safe" | "warning" | "danger",
                "checks": [
                    {"type": "allergy", "result": "safe|warning|danger", "detail": "..."},
                    {"type": "duplicate", ...},
                    {"type": "interaction", ...},
                ],
            }
        """
        checks = []
        drug = Drug.query.get(drug_id)
        if not drug:
            return {"overall": "safe", "checks": [], "error": "藥物不存在"}

        # 取得此藥物的成分 IDs
        drug_ing_ids = SafetyCheckService._get_drug_ingredient_ids(drug_id)

        # ── 1. 過敏檢查 ──
        allergy_result = SafetyCheckService._check_allergy(user_id, drug_ing_ids)
        checks.append(allergy_result)

        # ── 2. 重複用藥檢查 ──
        dup_result = SafetyCheckService._check_duplicate(
            user_id,
            drug_id,
            drug.name if hasattr(drug, "name") else drug.chinese_name,
            profile_id,
        )
        checks.append(dup_result)

        # ── 3. 交互作用檢查 ──
        interaction_result = SafetyCheckService._check_interactions(
            user_id, drug_ing_ids, profile_id
        )
        checks.append(interaction_result)

        # ── 4. 分級彙整 ──
        results = [c["result"] for c in checks]
        if "danger" in results:
            overall = "danger"
        elif "warning" in results:
            overall = "warning"
        else:
            overall = "safe"

        # 寫入 log
        for c in checks:
            if c["result"] != "safe":
                log = SafetyCheckLog(
                    user_id=user_id,
                    profile_id=profile_id,
                    drug_id=drug_id,
                    check_type=c["type"],
                    result=c["result"],
                    detail=c.get("detail", ""),
                )
                db.session.add(log)
        db.session.commit()

        return {"overall": overall, "checks": checks}

    # ── 內部方法 ──────────────────────────

    @staticmethod
    def _get_drug_ingredient_ids(drug_id: int) -> list[int]:
        rows = db.session.execute(
            drug_ingredients.select().where(drug_ingredients.c.drug_id == drug_id)
        ).fetchall()
        return [r.ingredient_id for r in rows]

    @staticmethod
    def _check_allergy(user_id: int, drug_ing_ids: list[int]) -> dict:
        if not drug_ing_ids:
            return {
                "type": "allergy",
                "result": "safe",
                "detail": "無成分資料，無法檢查過敏",
            }

        allergies = UserAllergy.query.filter(
            UserAllergy.user_id == user_id,
            UserAllergy.ingredient_id.in_(drug_ing_ids),
        ).all()

        if not allergies:
            return {"type": "allergy", "result": "safe", "detail": "無過敏風險"}

        names = [a.ingredient.name for a in allergies if a.ingredient]
        severities = [a.severity for a in allergies]
        worst = "danger" if "severe" in severities else "warning"
        return {
            "type": "allergy",
            "result": worst,
            "detail": f"過敏成分：{', '.join(names)}",
            "allergens": names,
        }

    @staticmethod
    def _check_duplicate(
        user_id: int, drug_id: int, drug_name: str, profile_id: Optional[int]
    ) -> dict:
        q = Medication.query.filter(
            Medication.user_id == user_id,
            Medication.is_active == True,  # noqa: E712
        )
        if profile_id:
            q = q.filter_by(profile_id=profile_id)

        # 同一 drug_id 或同名
        active = q.filter(
            db.or_(
                Medication.drug_id == drug_id,
                Medication.name == drug_name,
            )
        ).all()

        if not active:
            return {"type": "duplicate", "result": "safe", "detail": "無重複用藥"}

        dup_names = [m.name for m in active]
        return {
            "type": "duplicate",
            "result": "warning",
            "detail": f"已有相同用藥：{', '.join(dup_names)}",
            "duplicates": dup_names,
        }

    @staticmethod
    def _check_interactions(
        user_id: int, drug_ing_ids: list[int], profile_id: Optional[int]
    ) -> dict:
        if not drug_ing_ids:
            return {
                "type": "interaction",
                "result": "safe",
                "detail": "無成分資料，無法檢查交互",
            }

        # 取得使用者目前所有活躍用藥的成分
        q = Medication.query.filter(
            Medication.user_id == user_id,
            Medication.is_active == True,  # noqa: E712
        )
        if profile_id:
            q = q.filter_by(profile_id=profile_id)

        active_meds = q.all()
        active_drug_ids = [m.drug_id for m in active_meds if m.drug_id]

        if not active_drug_ids:
            return {
                "type": "interaction",
                "result": "safe",
                "detail": "無其他用藥，無交互風險",
            }

        # 取得所有活躍用藥的成分
        rows = db.session.execute(
            drug_ingredients.select().where(
                drug_ingredients.c.drug_id.in_(active_drug_ids)
            )
        ).fetchall()
        active_ing_ids = list({r.ingredient_id for r in rows})

        if not active_ing_ids:
            return {"type": "interaction", "result": "safe", "detail": "無成分資料"}

        # 查交互作用
        interactions = DrugInteraction.query.filter(
            db.or_(
                db.and_(
                    DrugInteraction.ingredient_a_id.in_(drug_ing_ids),
                    DrugInteraction.ingredient_b_id.in_(active_ing_ids),
                ),
                db.and_(
                    DrugInteraction.ingredient_a_id.in_(active_ing_ids),
                    DrugInteraction.ingredient_b_id.in_(drug_ing_ids),
                ),
            )
        ).all()

        if not interactions:
            return {"type": "interaction", "result": "safe", "detail": "無已知交互作用"}

        worst = "warning"
        details = []
        for ix in interactions:
            if ix.severity in ("severe", "contraindicated"):
                worst = "danger"
            details.append(
                {
                    "pair": f"{ix.ingredient_a.name} ↔ {ix.ingredient_b.name}",
                    "severity": ix.severity,
                    "description": ix.description,
                    "recommendation": ix.recommendation,
                }
            )

        return {
            "type": "interaction",
            "result": worst,
            "detail": f"發現 {len(details)} 組交互作用",
            "interactions": details,
        }
