"""
MUS2 壓力測試腳本（Locust）

使用方式:
    pip install locust
    locust -f locustfile.py --host http://localhost:5000

瀏覽器打開 http://localhost:8089 設定使用者數與 spawn rate。
"""

import json
import random
import string

from locust import HttpUser, between, task, events


def _random_username():
    return "load_" + "".join(random.choices(string.ascii_lowercase, k=8))


class MUS2User(HttpUser):
    """模擬一般使用者行為"""

    wait_time = between(1, 3)

    def on_start(self):
        """註冊 + 登入取得 JWT"""
        self.username = _random_username()
        self.password = "LoadTest1234"

        # 註冊
        self.client.post(
            "/api/auth/register",
            json={
                "username": self.username,
                "password": self.password,
            },
        )

        # 登入
        resp = self.client.post(
            "/api/auth/login",
            json={
                "username": self.username,
                "password": self.password,
            },
        )
        data = resp.json()
        self.access_token = data.get("access_token", "")
        self.refresh_token = data.get("refresh_token", "")
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

        # 建立 Profile
        resp = self.client.post(
            "/api/auth/profiles",
            json={"name": "壓測成員"},
            headers=self.headers,
        )
        profile_data = resp.json()
        self.profile_id = profile_data.get("profile", {}).get("id")

    # ── 高頻端點 ──

    @task(10)
    def health_check(self):
        self.client.get("/api/health")

    @task(5)
    def search_drug(self):
        queries = ["普拿疼", "阿斯匹靈", "感冒", "止痛", "消炎"]
        self.client.post(
            "/api/search",
            json={"query": random.choice(queries), "limit": 5},
        )

    @task(3)
    def get_me(self):
        self.client.get("/api/auth/me", headers=self.headers)

    @task(3)
    def list_profiles(self):
        self.client.get("/api/auth/profiles", headers=self.headers)

    @task(3)
    def list_medications(self):
        self.client.get("/api/user/medications", headers=self.headers)

    @task(2)
    def list_allergies(self):
        self.client.get("/api/safety/allergies", headers=self.headers)

    @task(2)
    def adherence_stats(self):
        self.client.get("/api/user/adherence/stats?days=7", headers=self.headers)

    @task(1)
    def list_interactions(self):
        self.client.get(
            "/api/safety/interactions?page=1&per_page=5", headers=self.headers
        )

    # ── 寫入端點（較低頻）──

    @task(1)
    def create_and_delete_medication(self):
        if not self.profile_id:
            return
        resp = self.client.post(
            "/api/user/medications",
            json={
                "name": f"壓測藥_{random.randint(1,999)}",
                "profile_id": self.profile_id,
                "dosage": "500mg",
                "frequency": "daily",
                "stock_qty": 10,
                "schedules": [
                    {"time_slot": "morning", "scheduled_time": "08:00", "dose_qty": 1}
                ],
            },
            headers=self.headers,
        )
        if resp.status_code == 201:
            med_id = resp.json().get("medication", {}).get("id")
            if med_id:
                self.client.delete(
                    f"/api/user/medications/{med_id}", headers=self.headers
                )

    @task(1)
    def refresh_token(self):
        if self.refresh_token:
            resp = self.client.post(
                "/api/auth/refresh",
                headers={"Authorization": f"Bearer {self.refresh_token}"},
            )
            if resp.status_code == 200:
                self.access_token = resp.json().get("access_token", self.access_token)
                self.headers = {"Authorization": f"Bearer {self.access_token}"}


class AdminUser(HttpUser):
    """模擬管理員：只打 health + metrics"""

    wait_time = between(5, 10)
    weight = 1  # 低權重

    @task
    def health(self):
        self.client.get("/api/health")

    @task
    def metrics(self):
        self.client.get("/admin/api/metrics")
