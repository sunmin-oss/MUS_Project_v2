"""Sprint 2 — Safety ORM schema 測試（S6-1/3/4/5）"""

import pytest


class TestSafetyModels:
    def test_ingredient_create(self, app, db_session):
        from models.safety import Ingredient

        ing = Ingredient(name="乙醯胺酚", name_en="Acetaminophen", category="解熱鎮痛")
        db_session.add(ing)
        db_session.commit()

        fetched = Ingredient.query.filter_by(name_en="Acetaminophen").first()
        assert fetched is not None
        assert fetched.name == "乙醯胺酚"
        assert fetched.to_dict()["category"] == "解熱鎮痛"

    def test_user_allergy_create(self, app, db_session):
        from models.user import User
        from models.safety import Ingredient, UserAllergy
        import uuid

        # 建立使用者 + 成分
        u = User(username=f"allergy_{uuid.uuid4().hex[:6]}", display_name="test")
        u.set_password("Test1234!")
        db_session.add(u)
        db_session.flush()

        ing = Ingredient(name=f"成分_{uuid.uuid4().hex[:6]}", name_en="TestIng")
        db_session.add(ing)
        db_session.flush()

        allergy = UserAllergy(user_id=u.id, ingredient_id=ing.id, severity="severe")
        db_session.add(allergy)
        db_session.commit()

        result = UserAllergy.query.filter_by(user_id=u.id).first()
        assert result is not None
        assert result.severity == "severe"
        assert result.to_dict()["ingredient_name"] == ing.name

    def test_safety_check_log_create(self, app, db_session):
        from models.safety import SafetyCheckLog

        log = SafetyCheckLog(
            check_type="allergy",
            result="warning",
            detail="測試過敏警告",
        )
        db_session.add(log)
        db_session.commit()

        fetched = SafetyCheckLog.query.first()
        assert fetched.check_type == "allergy"
        assert fetched.result == "warning"
