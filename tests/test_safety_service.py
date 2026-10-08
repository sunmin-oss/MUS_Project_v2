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
    def test_check_excludes_current_medication_from_duplicate(self, client, auth_tokens, app):
        hdr = auth_header(auth_tokens["access"])

        from models.drug import Drug

        with app.app_context():
            drug = Drug.query.first()
            if not drug:
                pytest.skip("測試資料庫沒有藥物資料")
            drug_id = drug.id
            drug_name = drug.chinese_name

        profile = client.post(
            "/api/auth/profiles",
            headers=hdr,
            json={"name": "本人", "relationship": "本人"},
        ).get_json()["profile"]
        medication = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "profile_id": profile["id"],
                "drug_id": drug_id,
                "name": drug_name,
                "start_date": "2026-05-27",
            },
        ).get_json()["medication"]

        response = client.post(
            "/api/safety/check",
            headers=hdr,
            json={
                "drug_id": drug_id,
                "profile_id": profile["id"],
                "medication_id": medication["id"],
            },
        )

        assert response.status_code == 200
        duplicate = next(
            check for check in response.get_json()["checks"] if check["type"] == "duplicate"
        )
        assert duplicate["result"] == "safe"

        second_medication = client.post(
            "/api/user/medications",
            headers=hdr,
            json={
                "profile_id": profile["id"],
                "drug_id": drug_id,
                "name": drug_name,
                "start_date": "2026-05-27",
            },
        ).get_json()["medication"]
        response = client.post(
            "/api/safety/check",
            headers=hdr,
            json={
                "drug_id": drug_id,
                "profile_id": profile["id"],
                "medication_id": medication["id"],
            },
        )

        duplicate = next(
            check for check in response.get_json()["checks"] if check["type"] == "duplicate"
        )
        assert duplicate["result"] == "warning"
        assert duplicate["duplicates"] == [second_medication["name"]]

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

    def test_check_existing_medication_does_not_match_itself(
        self, client, auth_tokens, app
    ):
        from datetime import date

        from models import db
        from models.drug import Drug
        from models.medication import Medication
        user_id = auth_tokens["user"]["id"]
        profile = client.post(
            "/api/auth/profiles",
            headers=auth_header(auth_tokens["access"]),
            json={"name": "本人", "relationship": "本人"},
        ).get_json()["profile"]
        with app.app_context():
            drug = Drug.query.first()
            drug_id = drug.id
            medication = Medication(
                user_id=user_id,
                profile_id=profile["id"],
                drug_id=drug_id,
                name=drug.chinese_name,
                start_date=date.today(),
            )
            db.session.add(medication)
            db.session.commit()
            medication_id = medication.id

        response = client.post(
            "/api/safety/check",
            headers=auth_header(auth_tokens["access"]),
            json={"drug_id": drug_id, "medication_id": medication_id},
        )

        duplicate = next(
            check
            for check in response.get_json()["checks"]
            if check["type"] == "duplicate"
        )
        assert duplicate["result"] == "safe"


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
