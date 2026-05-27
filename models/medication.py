"""
用藥管理 ORM Models（S1-1 / S1-2 / S1-7）

新增資料表：
- medications            用藥紀錄
- medication_schedules   用藥排程
- adherence_logs         服藥遵從紀錄
- push_tokens            推播 Token
"""

from datetime import datetime

from models import db


class Medication(db.Model):
    """用藥紀錄"""

    __tablename__ = "medications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    profile_id = db.Column(
        db.Integer, db.ForeignKey("profiles.id"), nullable=False, index=True
    )
    drug_id = db.Column(db.Integer, db.ForeignKey("drugs.id"), index=True)
    name = db.Column(db.String(128), nullable=False)
    dosage = db.Column(db.String(64))  # 例: "1 顆"、"5 ml"
    unit = db.Column(db.String(32))  # 顆 / ml / 包
    frequency = db.Column(db.String(32))  # daily / bid / tid / qid / prn
    duration_days = db.Column(db.Integer)  # 療程天數
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    stock_qty = db.Column(db.Integer)  # 庫存數量
    note = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref=db.backref("medications", lazy="dynamic"))
    profile = db.relationship("Profile")
    drug = db.relationship("Drug")
    schedules = db.relationship(
        "MedicationSchedule",
        backref="medication",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "profile_id": self.profile_id,
            "drug_id": self.drug_id,
            "name": self.name,
            "dosage": self.dosage,
            "unit": self.unit,
            "frequency": self.frequency,
            "duration_days": self.duration_days,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "stock_qty": self.stock_qty,
            "note": self.note,
            "is_active": self.is_active,
            "schedules": [s.to_dict() for s in self.schedules],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MedicationSchedule(db.Model):
    """用藥排程（每日各時段）"""

    __tablename__ = "medication_schedules"

    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(
        db.Integer, db.ForeignKey("medications.id"), nullable=False, index=True
    )
    time_slot = db.Column(
        db.String(16), nullable=False
    )  # morning / noon / evening / bedtime
    scheduled_time = db.Column(db.Time)  # 精確時間 HH:MM
    dose_qty = db.Column(db.Float, default=1.0)  # 該時段劑量

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "medication_id": self.medication_id,
            "time_slot": self.time_slot,
            "scheduled_time": (
                self.scheduled_time.strftime("%H:%M") if self.scheduled_time else None
            ),
            "dose_qty": self.dose_qty,
        }


class AdherenceLog(db.Model):
    """服藥遵從紀錄"""

    __tablename__ = "adherence_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    medication_id = db.Column(
        db.Integer, db.ForeignKey("medications.id"), nullable=False, index=True
    )
    schedule_id = db.Column(db.Integer, db.ForeignKey("medication_schedules.id"))
    status = db.Column(db.String(16), nullable=False)  # taken / skipped / late
    taken_at = db.Column(db.DateTime)
    scheduled_date = db.Column(db.Date, nullable=False, index=True)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")
    medication = db.relationship("Medication")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "medication_id": self.medication_id,
            "schedule_id": self.schedule_id,
            "status": self.status,
            "taken_at": self.taken_at.isoformat() if self.taken_at else None,
            "scheduled_date": (
                self.scheduled_date.isoformat() if self.scheduled_date else None
            ),
            "note": self.note,
        }


class PushToken(db.Model):
    """推播 Token（S1-2）"""

    __tablename__ = "push_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )
    token = db.Column(db.String(512), nullable=False, unique=True)
    platform = db.Column(db.String(16), nullable=False)  # ios / android / web
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref=db.backref("push_tokens", lazy="dynamic"))

    __table_args__ = (
        db.UniqueConstraint("user_id", "token", name="uq_user_push_token"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "platform": self.platform,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
