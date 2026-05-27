"""Sprint 3 — Safety Check Service + API 測試（S6-6 / S6-7）"""

import uuid
import pytest
from tests.conftest import auth_header


def _setup_user_with_allergy(client, app):
    """建立使用者 + 成分 + 過敏紀錄，回傳 (access_token, ingredient_id)"""
    username = f"safe_{uuid.uuid4().hex[:8]}"
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "Test1234!",
        },
    )
    login = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": "Test1234!",
        },
    )
    token = login.get_json()["access_token"]
    hdr = auth_header(token)

    # 建立成分
    from models import db
    from models.safety import Ingredient

    with app.app_context():
        ing = Ingredient(name=f"測試成分_{uuid.uuid4().hex[:6]}", name_en="TestAllIng")
        db.session.add(ing)
        db.session.commit()
        ing_id = ing.id

    # 加入過敏
    client.post(
        "/api/safety/allergies",
        headers=hdr,
        json={
            "ingredient_id": ing_id,
            "severity": "severe",
        },
    )

    return token, ing_id


class TestSafetyCheck:
    def test_check_safe(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        # drug_id=1 假設存在（已有資料庫）
        resp = client.post("/api/safety/check", headers=hdr, json={"drug_id": 1})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["overall"] in ("safe", "warning", "danger")

    def test_check_missing_drug_id(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        resp = client.post("/api/safety/check", headers=hdr, json={})
        assert resp.status_code == 400

    def test_check_no_auth(self, client):
        resp = client.post("/api/safety/check", json={"drug_id": 1})
        assert resp.status_code == 401


class TestAllergiesCRUD:
    def test_add_allergy(self, client, auth_tokens, app):
        hdr = auth_header(auth_tokens["access"])
        from models import db
        from models.safety import Ingredient

        with app.app_context():
            ing = Ingredient(name=f"成分_{uuid.uuid4().hex[:6]}", name_en="AlgIng")
            db.session.add(ing)
            db.session.commit()
            ing_id = ing.id

        resp = client.post(
            "/api/safety/allergies",
            headers=hdr,
            json={
                "ingredient_id": ing_id,
                "severity": "moderate",
            },
        )
        assert resp.status_code == 201
        assert resp.get_json()["allergy"]["severity"] == "moderate"

    def test_list_allergies(self, client, auth_tokens, app):
        hdr = auth_header(auth_tokens["access"])
        from models import db
        from models.safety import Ingredient

        with app.app_context():
            ing = Ingredient(name=f"成分_{uuid.uuid4().hex[:6]}")
            db.session.add(ing)
            db.session.commit()
            ing_id = ing.id
        client.post(
            "/api/safety/allergies", headers=hdr, json={"ingredient_id": ing_id}
        )
        resp = client.get("/api/safety/allergies", headers=hdr)
        assert resp.status_code == 200
        assert len(resp.get_json()["allergies"]) >= 1

    def test_delete_allergy(self, client, auth_tokens, app):
        hdr = auth_header(auth_tokens["access"])
        from models import db
        from models.safety import Ingredient

        with app.app_context():
            ing = Ingredient(name=f"成分_{uuid.uuid4().hex[:6]}")
            db.session.add(ing)
            db.session.commit()
            ing_id = ing.id
        create = client.post(
            "/api/safety/allergies", headers=hdr, json={"ingredient_id": ing_id}
        )
        aid = create.get_json()["allergy"]["id"]
        resp = client.delete(f"/api/safety/allergies/{aid}", headers=hdr)
        assert resp.status_code == 200

    def test_duplicate_allergy(self, client, auth_tokens, app):
        hdr = auth_header(auth_tokens["access"])
        from models import db
        from models.safety import Ingredient

        with app.app_context():
            ing = Ingredient(name=f"成分_{uuid.uuid4().hex[:6]}")
            db.session.add(ing)
            db.session.commit()
            ing_id = ing.id
        client.post(
            "/api/safety/allergies", headers=hdr, json={"ingredient_id": ing_id}
        )
        resp = client.post(
            "/api/safety/allergies", headers=hdr, json={"ingredient_id": ing_id}
        )
        assert resp.status_code == 409


class TestInteractionsAPI:
    def test_list_interactions(self, client, auth_tokens):
        hdr = auth_header(auth_tokens["access"])
        resp = client.get("/api/safety/interactions", headers=hdr)
        assert resp.status_code == 200
        data = resp.get_json()
        assert "interactions" in data
        assert "total" in data
