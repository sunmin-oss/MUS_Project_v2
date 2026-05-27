"""
S6-2: 寫入 ≥ 10 筆 demo 藥物交互作用資料

使用方式:
    python scripts/seed_interactions.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEMO_INGREDIENTS = [
    {"name": "乙醯胺酚", "name_en": "Acetaminophen", "category": "解熱鎮痛"},
    {"name": "阿斯匹靈", "name_en": "Aspirin", "category": "解熱鎮痛/抗血小板"},
    {"name": "布洛芬", "name_en": "Ibuprofen", "category": "非類固醇抗發炎"},
    {"name": "華法林", "name_en": "Warfarin", "category": "抗凝血"},
    {"name": "甲福明", "name_en": "Metformin", "category": "降血糖"},
    {"name": "氫氯噻嗪", "name_en": "Hydrochlorothiazide", "category": "利尿劑"},
    {"name": "辛伐他汀", "name_en": "Simvastatin", "category": "降血脂"},
    {"name": "紅黴素", "name_en": "Erythromycin", "category": "巨環類抗生素"},
    {"name": "氟康唑", "name_en": "Fluconazole", "category": "抗黴菌"},
    {"name": "鋰鹽", "name_en": "Lithium", "category": "情緒穩定劑"},
    {"name": "地高辛", "name_en": "Digoxin", "category": "強心苷"},
    {"name": "西咪替丁", "name_en": "Cimetidine", "category": "H2受體拮抗劑"},
]

DEMO_INTERACTIONS = [
    {
        "a": "華法林",
        "b": "阿斯匹靈",
        "severity": "severe",
        "description": "併用會顯著增加出血風險",
        "mechanism": "阿斯匹靈抑制血小板聚集，華法林抑制凝血因子，兩者協同增加出血",
        "recommendation": "避免併用，若必須使用需密切監測 INR",
        "source": "UpToDate / FDA",
    },
    {
        "a": "華法林",
        "b": "布洛芬",
        "severity": "severe",
        "description": "NSAIDs 增加華法林所致出血風險",
        "mechanism": "布洛芬抑制 COX-1 影響血小板、損傷胃黏膜，加上華法林的抗凝血效果",
        "recommendation": "盡量避免併用，改用乙醯胺酚做替代鎮痛",
        "source": "UpToDate",
    },
    {
        "a": "辛伐他汀",
        "b": "紅黴素",
        "severity": "contraindicated",
        "description": "紅黴素為強效 CYP3A4 抑制劑，會大幅升高 Statin 血中濃度",
        "mechanism": "CYP3A4 抑制導致辛伐他汀無法代謝，增加橫紋肌溶解症風險",
        "recommendation": "禁忌併用，改用不經 CYP3A4 代謝的 Statin",
        "source": "FDA Black Box Warning",
    },
    {
        "a": "辛伐他汀",
        "b": "氟康唑",
        "severity": "severe",
        "description": "氟康唑抑制 CYP3A4，升高辛伐他汀濃度",
        "mechanism": "CYP3A4 抑制，增加肌肉毒性風險",
        "recommendation": "考慮暫停辛伐他汀或改用其他 Statin",
        "source": "UpToDate",
    },
    {
        "a": "布洛芬",
        "b": "鋰鹽",
        "severity": "severe",
        "description": "NSAIDs 減少鋰鹽腎排泄，導致鋰中毒",
        "mechanism": "布洛芬減少腎血流量及鋰鹽清除率",
        "recommendation": "併用時需密切監測血鋰濃度",
        "source": "UpToDate",
    },
    {
        "a": "布洛芬",
        "b": "氫氯噻嗪",
        "severity": "moderate",
        "description": "NSAIDs 可能降低利尿劑的降壓效果",
        "mechanism": "NSAIDs 促進鈉水滯留，抵消利尿劑效果",
        "recommendation": "監測血壓，必要時調整利尿劑劑量",
        "source": "UpToDate",
    },
    {
        "a": "甲福明",
        "b": "西咪替丁",
        "severity": "moderate",
        "description": "西咪替丁抑制甲福明腎排泄，升高血中濃度",
        "mechanism": "競爭腎小管分泌",
        "recommendation": "監測甲福明血中濃度及腎功能",
        "source": "Lexicomp",
    },
    {
        "a": "地高辛",
        "b": "氫氯噻嗪",
        "severity": "severe",
        "description": "利尿劑致低血鉀會增加地高辛毒性",
        "mechanism": "低血鉀增強地高辛與鈉鉀 ATPase 結合",
        "recommendation": "監測電解質，補充鉀離子",
        "source": "UpToDate",
    },
    {
        "a": "阿斯匹靈",
        "b": "布洛芬",
        "severity": "moderate",
        "description": "布洛芬可能降低阿斯匹靈的抗血小板效果",
        "mechanism": "布洛芬競爭性佔據 COX-1 結合位，阻礙阿斯匹靈的不可逆乙醯化",
        "recommendation": "若需併用，阿斯匹靈應至少提前 30 分鐘服用",
        "source": "FDA Advisory",
    },
    {
        "a": "紅黴素",
        "b": "華法林",
        "severity": "moderate",
        "description": "紅黴素可能增強華法林抗凝效果",
        "mechanism": "紅黴素抑制 CYP3A4 / CYP1A2，減少華法林代謝",
        "recommendation": "加強 INR 監測，必要時調整華法林劑量",
        "source": "UpToDate",
    },
    {
        "a": "氟康唑",
        "b": "華法林",
        "severity": "severe",
        "description": "氟康唑顯著增強華法林抗凝效果",
        "mechanism": "氟康唑抑制 CYP2C9，華法林 S-異構體的主要代謝酶",
        "recommendation": "減少華法林劑量約 25-50%，密切監測 INR",
        "source": "FDA / UpToDate",
    },
    {
        "a": "地高辛",
        "b": "紅黴素",
        "severity": "moderate",
        "description": "紅黴素可能升高地高辛血中濃度",
        "mechanism": "紅黴素抑制腸道菌群對地高辛的代謝、抑制 P-gp 外排",
        "recommendation": "監測地高辛血中濃度",
        "source": "Lexicomp",
    },
]


def seed():
    from main import app
    from models import db
    from models.safety import Ingredient, DrugInteraction

    with app.app_context():
        db.create_all()

        # 1. 建立成分
        ing_map = {}
        for item in DEMO_INGREDIENTS:
            existing = Ingredient.query.filter_by(name=item["name"]).first()
            if existing:
                ing_map[item["name"]] = existing
            else:
                ing = Ingredient(**item)
                db.session.add(ing)
                db.session.flush()
                ing_map[item["name"]] = ing

        # 2. 建立交互作用
        created = 0
        for ix in DEMO_INTERACTIONS:
            a = ing_map[ix["a"]]
            b = ing_map[ix["b"]]
            # 確保 a_id < b_id 以維持一致性
            a_id, b_id = (a.id, b.id) if a.id < b.id else (b.id, a.id)
            existing = DrugInteraction.query.filter_by(
                ingredient_a_id=a_id, ingredient_b_id=b_id
            ).first()
            if not existing:
                db.session.add(
                    DrugInteraction(
                        ingredient_a_id=a_id,
                        ingredient_b_id=b_id,
                        severity=ix["severity"],
                        description=ix["description"],
                        mechanism=ix.get("mechanism"),
                        recommendation=ix.get("recommendation"),
                        source=ix.get("source"),
                    )
                )
                created += 1

        db.session.commit()
        print(f"✓ 成分: {len(ing_map)} 筆, 新增交互作用: {created} 筆")


if __name__ == "__main__":
    seed()
