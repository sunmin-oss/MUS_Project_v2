"""
用藥安全 ORM Models（S6-1 / S6-3 / S6-4 / S6-5）

新增資料表：
- ingredients         成分表
- drug_ingredients    藥物-成分 多對多
- user_allergies      使用者過敏紀錄
- safety_check_logs   安全檢查紀錄
"""

from datetime import datetime

from models import db


# ── S6-1  成分表 ──────────────────────────
class Ingredient(db.Model):
    """藥物成分"""

    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True, index=True)
    name_en = db.Column(db.String(128), index=True)
    category = db.Column(db.String(64))  # 例: 解熱鎮痛 / 抗組織胺 …
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "name_en": self.name_en,
            "category": self.category,
        }


# ── S6-1  藥物-成分 關聯表 ─────────────────
drug_ingredients = db.Table(
    "drug_ingredients",
    db.Column("drug_id", db.Integer, db.ForeignKey("drugs.id"), primary_key=True),
    db.Column(
        "ingredient_id", db.Integer, db.ForeignKey("ingredients.id"), primary_key=True
    ),
)


# ── S6-3  使用者過敏紀錄 ───────────────────
class UserAllergy(db.Model):
    """使用者過敏成分"""

    __tablename__ = "user_allergies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    ingredient_id = db.Column(
        db.Integer, db.ForeignKey("ingredients.id"), nullable=False
    )
    severity = db.Column(db.String(16), default="moderate")  # mild / moderate / severe
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("allergies", lazy="dynamic"))
    ingredient = db.relationship("Ingredient")

    __table_args__ = (
        db.UniqueConstraint("user_id", "ingredient_id", name="uq_user_ingredient"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ingredient_id": self.ingredient_id,
            "ingredient_name": self.ingredient.name if self.ingredient else None,
            "severity": self.severity,
            "note": self.note,
        }


# ── S6-4 / S6-5  安全檢查紀錄 ──────────────
class SafetyCheckLog(db.Model):
    """用藥安全檢查紀錄"""

    __tablename__ = "safety_check_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), index=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profiles.id"))
    drug_id = db.Column(db.Integer, db.ForeignKey("drugs.id"))
    check_type = db.Column(
        db.String(32), nullable=False
    )  # allergy / interaction / duplicate
    result = db.Column(db.String(16), nullable=False)  # safe / warning / danger
    detail = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    profile = db.relationship("Profile")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "profile_id": self.profile_id,
            "drug_id": self.drug_id,
            "check_type": self.check_type,
            "result": self.result,
            "detail": self.detail,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
