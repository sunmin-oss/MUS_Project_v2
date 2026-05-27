# 後端 Sprint 衝刺規劃單（Backend Sprint Plan）

> 文件版本：v1.0
> 對應路線圖：[BACKEND_ROADMAP.md](./BACKEND_ROADMAP.md)
> 對應 App 端：[APP_ROADMAP.md](./APP_ROADMAP.md)
> **競賽 deadline：2026-06-30**
> 衝刺起點：2026-05-27
> 團隊：2 人（Dev A / Dev B）

---

## 1. 目標與範圍

### 1.1 競賽範圍 MVP（必須完成）

| 模組 | 對應 Roadmap | 對應 App |
|---|---|---|
| **A-3** 爬蟲 Quick Win | A-3 方案 A | 不直接相關，但需資料庫即時 |
| **A-1** Auth + Profile | A-1（精簡版） | Phase 1 全模組 |
| **Spec 01** Medications + Push | S1-1~S1-7 | P1B + P1E |
| **Spec 06** Safety Check | S6-1~S6-8 | P1D |

### 1.2 砍除（移至 Phase 2，6/30 後）

- Apple / Google OAuth（A1-5、A1-6）
- Email OTP 密碼重設（A1-7）
- PDPA 帳號刪除（A1-10）
- 處方箋 OCR（S1-8 ~ S1-10）
- PostgreSQL 遷移 + Alembic
- 交互作用商業資料庫（先空表 + 手動寫入 demo 資料）
- 訂閱 / 額度管理（A-2，整支延後）

### 1.3 對齊 App 端的硬性截止點

| 後端交付物 | 截止日 | 對應 App 任務 |
|---|---|---|
| Auth API（註冊/登入/JWT 中介層） | **6/9** | App W3 開始接 |
| Medications + Push Token API | **6/16** | App W3 用藥模組 |
| Safety Check API | **6/23** | App W4 安全警示 |
| 整體穩定 + 文件 | **6/30** | App W5 Demo |

---

## 2. 團隊分工

| 角色 | 主責 | 次責 |
|---|---|---|
| **Dev A** | Auth / Medications / Push | ORM / Blueprint |
| **Dev B** | Crawler / Safety / 資料模組 | 測試 / Migration |

每日 15 分鐘同步、每週 Sprint Review。

---

## 3. Sprint 排程（5 個 1 週 Sprint）

### Sprint 1（5/27 ~ 6/2）— 基礎建設 + 爬蟲加速

| Dev A | Dev B |
|---|---|
| **P0-1** SQLAlchemy 包裝既有 4 張表 | **A3-1** 重構 `nhi_crawler.py`，抽出 Browser 注入 |
| **P0-3** Blueprint 拆 `/auth`、`/user`、`/safety` | **A3-2** 移除所有 `wait_for_timeout`，改 `wait_for_selector` |
| **A1-1** `users` / `profiles` schema + ORM Model | **A3-3** 移除 debug 寫檔 |
| **A1-2** bcrypt + `POST /api/auth/register` | **A3-4** `delay=0.5s` + 失敗指數退避 |
| **P0-4** pytest 框架 + fixtures | **A3-5** DB 連線共用 + `PRAGMA journal_mode=WAL` |

**Sprint 1 Demo（6/2）**：
- 可呼叫 `/api/auth/register` 註冊（明文/加密測試）
- 爬蟲全表 benchmark ≤ 1.5 小時（A3-7）
- 測試框架可跑單元測試

### Sprint 2（6/3 ~ 6/9）— Auth 完備 ⚠️ App W3 依賴

| Dev A | Dev B |
|---|---|
| **A1-3** JWT Access + Refresh Token | **S6-1** `ingredients` + `drug_ingredients` schema |
| **A1-4** `@jwt_required` 中介層 + `current_user` helper | **S6-3** `user_allergies` schema + CRUD |
| **A1-8** Profile CRUD（多人成員） | **S6-4** `drug_safety_profiles` schema |
| **A1-9** `/api/recognize` 加入可選 JWT + 紀錄歷史 | **S6-5** `safety_check_logs` schema |
| **P0-5** Rate Limit + Error Handler 中介層 | **A3-6** Admin batch update 端點補 `throughput` 指標 |

**Sprint 2 交付（6/9）⚠️ 關鍵節點**：
- ✅ **Auth API 完成**：`POST /api/auth/register`、`/login`、`/refresh`、`/logout`
- ✅ **Profile API 完成**：`/api/user/profiles` GET/POST/PUT/DELETE
- ✅ JWT 中介層全線就緒
- App 端可開始 W3 開發

### Sprint 3（6/10 ~ 6/16）— Medications + Safety Service ⚠️ App W3 依賴

| Dev A | Dev B |
|---|---|
| **S1-1** `medications` + `medication_schedules` + CRUD | **S6-6** `SafetyCheckService`：過敏 → 重複 → 交互 → 分級 |
| **S1-2** `push_tokens` schema + 註冊端點 | **S6-7** `POST /api/safety/check` + `GET /api/safety/interactions` |
| **S1-7** `adherence_logs` + 端點（日曆 / 統計） | **S6-2** `drug_interactions` 空表 + 手動寫入 ≥ 10 筆 demo 資料 |
| `/api/user/medications` 全套 API | `/api/safety/*` 全套 API |

**Sprint 3 交付（6/16）⚠️ 關鍵節點**：
- ✅ **Medications API 完成**：用藥 CRUD + 排程 + 紀錄
- ✅ **Push Token 註冊端點**完成
- ✅ **Safety Check API 完成**（含 demo 用交互作用資料）
- App 端可開始 W4 開發

### Sprint 4（6/17 ~ 6/23）— 推播 + 整合 ⚠️ App W4 依賴

| Dev A | Dev B |
|---|---|
| **S1-3** APScheduler 單機整合 | `/api/recognize` 串接 `SafetyCheckService` |
| **S1-5** APNs iOS 推播（含 p8 key 設定） | **S6-8** 辨識結果回傳安全警示 |
| **S1-6** 排程掃描 → 觸發推播任務 | E2E pytest：用藥 → 排程 → 推播全鏈路 |
| 補藥提醒（庫存倒數） | E2E pytest：辨識 → 安全檢查 |

**Sprint 4 交付（6/23）⚠️ 關鍵節點**：
- ✅ **iOS 實機可收到推播**（提早備好測試機 + APNs 憑證）
- ✅ 辨識完成後自動回傳安全警示
- App 端可進入 W5 整合測試

### Sprint 5（6/24 ~ 6/30）— 穩定化 + Demo 準備

| 共同任務 |
|---|
| Bug fix + 壓測（locust 或 ab） |
| API 文件（OpenAPI / Postman collection） |
| Rate Limit 調校 |
| Staging 部署（Docker + nginx） |
| 與 App 端聯合 Demo 演練 |
| 監控指標（請求數、錯誤率、平均延遲） |
| Release `v3.0.0` Tag |

**Sprint 5 交付（6/30）**：
- ✅ 後端 staging 上線、穩定可 demo
- ✅ Tag `v3.0.0`、文件齊備

---

## 4. 緩衝與風險

### 4.1 緩衝設計

- 每個 Sprint 末預留 1 天緩衝（週日）
- Sprint 5 整週為緩衝 + 拋光，**不安排新功能**
- 若 Sprint 2 / 3 落後，啟動下方降級方案

### 4.2 降級方案（Fallback）

| 風險 | 觸發條件 | 降級方案 |
|---|---|---|
| Auth API 6/9 未完成 | Sprint 2 結束未交付 | 退用 API Key 認證（單一硬編碼 Key），App 仍能串接 |
| Push 推播 6/23 未完成 | APNs 憑證問題 | App 改用本地排程（UNUserNotificationCenter），後端只存設定 |
| Safety Service 6/23 未完成 | S6-6 邏輯複雜 | 砍 4 層為 2 層（只做過敏 + 重複），交互/分級延 Phase 2 |
| 全面失守 | Sprint 4 仍未到 80% | App 啟用 Demo 模式（純 Mock），後端只保留 v2.0.2 功能 |

### 4.3 必要外部依賴

- [ ] **APNs p8 key + Team ID**（Apple Developer 帳號，App 端負責申請）— Sprint 3 前到位
- [ ] iOS **實機**測試裝置（模擬器無法測 APNs）— Sprint 4 前到位
- [ ] Production 伺服器 / VPS（Sprint 5 部署用）— Sprint 4 前確認

---

## 5. 分支策略

依 [CONTRIBUTING.md](../CONTRIBUTING.md) 規範，每個任務群一條 feature 分支從 `develop` 開：

| Sprint | 分支名 | 涵蓋任務 |
|---|---|---|
| 1 | `feature/db-orm-sqlalchemy` | P0-1, P0-3 |
| 1 | `feature/crawler-perf-quickwin` | A3-1 ~ A3-7 |
| 1 | `feature/auth-register-bcrypt` | A1-1, A1-2, P0-4 |
| 2 | `feature/auth-jwt` | A1-3, A1-4, A1-9 |
| 2 | `feature/user-profiles` | A1-8 |
| 2 | `feature/safety-schema` | S6-1, S6-3, S6-4, S6-5 |
| 2 | `feature/middleware-ratelimit` | P0-5 |
| 3 | `feature/medications-crud` | S1-1, S1-2, S1-7 |
| 3 | `feature/safety-check-service` | S6-2, S6-6, S6-7 |
| 4 | `feature/push-notifications` | S1-3, S1-5, S1-6 |
| 4 | `feature/recognize-safety-integration` | S6-8 |
| 5 | `release/v3.0.0` | 整合、Tag |

---

## 6. 驗收清單（DoD: Definition of Done）

每個任務完成必須通過：

- [ ] 程式碼合到 `develop`，PR 通過 self-review
- [ ] 對應的 pytest 單元測試 ≥ 1 條，CI 通過
- [ ] API 端點以 `curl` / Postman 實際呼叫成功
- [ ] 文件：API 端點寫入 `docs/API.md`（Sprint 5 整理）
- [ ] 至少在開發機完成一次 E2E 測試

---

## 7. 進度追蹤

- **每週五**：更新本檔案 §3 各 Sprint 的勾選狀態
- **GitHub Issues**：每個任務一個 issue，依 milestone（Sprint 1 ~ 5）分組
- **看板**：GitHub Project（status: Todo / In Progress / Review / Done）

---

## 8. 立即下一步

1. 切第一條工作分支：`feature/crawler-perf-quickwin`（Dev B）+ `feature/db-orm-sqlalchemy`（Dev A）
2. 開 GitHub Milestones × 5（對應 Sprint 1~5，截止日 6/2, 6/9, 6/16, 6/23, 6/30）
3. 開 GitHub Issues × 約 35 個（見 §3 Sprint 任務）
4. 與 App 端確認 APNs 憑證 / 測試機準備時程
