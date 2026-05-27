"""
藥物相關 ORM Model

對應既有資料表（請勿在此檔修改欄位定義，需透過 Alembic migration）：
- drugs            主檔
- drug_images      圖片
- nhi_cache        健保署資料快取
- api_logs         API 呼叫紀錄
"""

from datetime import datetime

from models import db


class Drug(db.Model):
    """藥物主檔（對應 drugs 表）"""

    __tablename__ = "drugs"

    id = db.Column(db.Integer, primary_key=True)
    license_number = db.Column(db.Text, nullable=False, unique=True, index=True)
    chinese_name = db.Column(db.Text, nullable=False, index=True)
    english_name = db.Column(db.Text, index=True)
    shape = db.Column(db.Text, index=True)
    special_dosage_form = db.Column(db.Text)
    color = db.Column(db.Text, index=True)
    special_odor = db.Column(db.Text)
    mark = db.Column(db.Text)
    size = db.Column(db.Text)
    label_front = db.Column(db.Text)
    label_back = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # NHI 詳細資料欄位
    indications = db.Column(db.Text)
    dosage = db.Column(db.Text)
    side_effects = db.Column(db.Text)
    contraindications = db.Column(db.Text)
    precautions = db.Column(db.Text)
    ingredient = db.Column(db.Text)
    category = db.Column(db.Text)
    manufacturer = db.Column(db.Text)
    storage_conditions = db.Column(db.Text)
    expiry_info = db.Column(db.Text)

    # 關聯
    images = db.relationship(
        "DrugImage", backref="drug", lazy="dynamic", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "license_number": self.license_number,
            "chinese_name": self.chinese_name,
            "english_name": self.english_name,
            "shape": self.shape,
            "color": self.color,
            "ingredient": self.ingredient,
            "manufacturer": self.manufacturer,
            "indications": self.indications,
            "dosage": self.dosage,
            "side_effects": self.side_effects,
            "contraindications": self.contraindications,
            "precautions": self.precautions,
            "category": self.category,
        }

    def __repr__(self) -> str:
        return f"<Drug {self.id} {self.chinese_name}>"


class DrugImage(db.Model):
    """藥物圖片（對應 drug_images 表）"""

    __tablename__ = "drug_images"

    id = db.Column(db.Integer, primary_key=True)
    drug_id = db.Column(
        db.Integer, db.ForeignKey("drugs.id"), nullable=False, index=True
    )
    image_filename = db.Column(db.Text, nullable=False, index=True)
    image_path = db.Column(db.Text, nullable=False)
    image_order = db.Column(db.Integer, default=0)
    feature_vector = db.Column(db.Text)  # JSON 字串，後續可改 JSON 型別
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<DrugImage {self.id} drug={self.drug_id} {self.image_filename}>"


class NhiCache(db.Model):
    """健保署查詢快取（對應 nhi_cache 表）"""

    __tablename__ = "nhi_cache"

    drug_id = db.Column(db.Integer, primary_key=True)
    search_name = db.Column(db.Text, nullable=False)
    nhi_data = db.Column(db.Text, nullable=False)  # JSON 字串
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<NhiCache drug_id={self.drug_id} name={self.search_name}>"


class ApiLog(db.Model):
    """API 呼叫紀錄（對應 api_logs 表）"""

    __tablename__ = "api_logs"

    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.Text)
    method = db.Column(db.Text)
    status_code = db.Column(db.Integer)
    duration_ms = db.Column(db.Float)
    query_params = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<ApiLog {self.id} {self.method} {self.endpoint} {self.status_code}>"
