"""
家庭成員 Profile ORM Model（A1-8）

新增資料表：
- profiles  家庭成員檔案
"""

from datetime import datetime

from models import db


class Profile(db.Model):
    """家庭成員檔案（多成員）"""

    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    name = db.Column(db.String(64), nullable=False)
    relationship = db.Column(db.String(32))  # 本人 / 父親 / 母親 …
    birth_date = db.Column(db.Date)
    allergies = db.Column(db.Text)  # JSON 字串，日後 S6 會正規化
    note = db.Column(db.Text)
    is_default = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref=db.backref("profiles", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "relationship": self.relationship,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "allergies": self.allergies,
            "note": self.note,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Profile {self.id} {self.name} (user={self.user_id})>"
