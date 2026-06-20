# 程式碼片段 4：四層用藥安全檢查 (services/__init__.py)
# 用途：論文 3.6 節 — 用藥安全檢查機制

class SafetyCheckService:
    """用藥安全檢查服務"""

    @staticmethod
    def check(user_id, drug_id, profile_id=None):
        """對指定藥物執行四層安全檢查"""
        checks = []
        drug = Drug.query.get(drug_id)
        drug_ing_ids = SafetyCheckService._get_drug_ingredient_ids(drug_id)

        # ── 第 1 層：過敏檢查 ──
        allergy_result = SafetyCheckService._check_allergy(user_id, drug_ing_ids)
        checks.append(allergy_result)

        # ── 第 2 層：重複用藥檢查 ──
        dup_result = SafetyCheckService._check_duplicate(
            user_id, drug_id, drug.chinese_name, profile_id
        )
        checks.append(dup_result)

        # ── 第 3 層：交互作用檢查 ──
        interaction_result = SafetyCheckService._check_interactions(
            user_id, drug_ing_ids, profile_id
        )
        checks.append(interaction_result)

        # ── 第 4 層：分級彙整 ──
        results = [c["result"] for c in checks]
        if "danger" in results:
            overall = "danger"
        elif "warning" in results:
            overall = "warning"
        else:
            overall = "safe"

        # 寫入安全檢查紀錄
        for c in checks:
            if c["result"] != "safe":
                log = SafetyCheckLog(
                    user_id=user_id, drug_id=drug_id,
                    check_type=c["type"], result=c["result"],
                    detail=c.get("detail", "")
                )
                db.session.add(log)
        db.session.commit()

        return {"overall": overall, "checks": checks}
