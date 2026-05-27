# 後端開發規劃單（Backend Development Roadmap）

> 文件版本：v1.0 Draft
> 對應 Feature Specs：01–06（docs/features/）
> 現有後端技術棧：Flask + SQLite + Vision API（Gemini/Claude/Google）

---

## 現有後端架構摘要

```
Flask App (main.py)
 ├─ /api/health              系統狀態
 ├─ /api/recognize           藥品辨識（圖片 → Vision API → RAG → DB）
 ├─ /api/search              藥品名稱搜尋
 ├─ /api/drug/<id>           藥品詳細資訊
 └─ /admin/*                 管理後台（admin_routes.py）

SQLite DB (drug_recognition.db)
 ├─ drugs                    藥品基本資料
 ├─ drug_images              藥品圖片
 ├─ nhi_cache                健保快取
 └─ api_logs                 API 使用紀錄

Vision APIs: Gemini / Claude / Google Vision（可動態切換）
```

**需要改變的核心架構決策**：
- SQLite → 評估遷移至 **PostgreSQL**（多使用者並發、關聯複雜度增加）
- 加入 **JWT 身份驗證**（現有後端無使用者系統）
- 加入 **WebSocket** 支援（即時諮詢對話）
- 加入 **排程任務**（推播、補藥提醒）
- 加入 **訂閱/額度管理**中介層

---

## 架構升級需求（所有 Feature 的前置條件）

### A-1：使用者帳號系統（所有 Feature 的基礎）

**目前狀態**：無使用者系統，所有 API 公開無驗證

**需要開發**：
- `users` 資料表（id, email, password_hash, subscription_tier, created_at）
- `profiles` 資料表（id, user_id, name, birth_date, gender, weight, is_primary）
- JWT 登入 / 登出 / Refresh Token
- OAuth 登入（Apple / Google，行動 App 必備）
- 密碼重設流程（Email OTP）
- 中介層（Middleware）：所有 `/api/user/*` 端點需驗證 JWT

**新增端點**：
```
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
POST /api/auth/refresh
POST /api/auth/oauth/apple
POST /api/auth/oauth/google
POST /api/auth/forgot-password
POST /api/auth/reset-password

GET  /api/user/profiles
POST /api/user/profiles
PUT  /api/user/profiles/<id>
DEL  /api/user/profiles/<id>
```

**影響現有 API**：
- `/api/recognize` 需加入可選 JWT（未登入仍可用，但計入匿名額度）

---

### A-2：訂閱與額度管理系統

**目前狀態**：無

**需要開發**：
- `subscriptions` 資料表（user_id, tier, start_at, end_at, store_receipt）
- `usage_quotas` 資料表（user_id, feature, count, reset_date）
- 訂閱驗證中介層（每個受限端點檢查 tier + quota）
- Apple StoreKit / Google Play Billing 收據驗證端點
- Quota 每月重置排程任務

**新增端點**：
```
GET  /api/subscription/status
POST /api/subscription/verify-receipt   (Apple/Google)
POST /api/subscription/cancel
GET  /api/subscription/usage            (查看本月額度使用量)
```

**額度規則**（對應 spec 05）：
| Feature Key | Free | Pro |
|---|---|---|
| drug_recognize | 5/天 | 無限 |
| prescription_ocr | 1/月 | 無限 |
| ai_consultation | 3/月 | 無限 |
| pdf_export | 0 | 無限 |

---

### A-3：藥品資料更新爬蟲效能優化（資料維運）

**目前狀態**：
- `scripts/nhi_crawler.py` 使用 Playwright 逐筆爬取 NHI / TFDA
- `scripts/batch_update.py` 以單執行緒 `for` 迴圈呼叫，搭配固定 `delay`（預設 3s）
- 全表 **4000 筆需 ~11 小時**（約 10 秒/筆），無法支撐後續 Feature 對最新藥品資料的需求

**瓶頸分析**：
| # | 位置 | 單筆耗時 | 問題 |
|---|---|---|---|
| 1 | 每筆都 `p.chromium.launch()` | 1–2s | Browser 未重用 |
| 2 | `wait_for_timeout(3000)` 搜尋後硬等 | 3s | 應改顯式等待 |
| 3 | `wait_for_timeout(5000)` 詳情頁硬等 | 5s | 應改顯式等待 |
| 4 | `wait_for_timeout(2000)` 圖片 tab 硬等 | 2s | 應改顯式等待 |
| 5 | `time.sleep(self.delay)` 預設 3s | 3s | 應採成功 0.5s / 失敗指數退避 |
| 6 | 每筆寫 `tfda_detail_page_debug.txt` | ~50ms | 僅 debug 用途，正式跑無意義 |
| 7 | 全程單執行緒 `for` 迴圈 | — | 無並發 |
| 8 | 每筆 sqlite 連線開關 2 次 | ~30ms | 應共用連線、批次 commit |

**優化方案（分階段）**：

| 方案 | 內容 | 預估全表耗時 | 提速 | 成本 |
|---|---|---|---|---|
| 現況 | — | 11 小時 | 1× | — |
| **A** Quick Win | Browser 重用、移除硬等、`wait_for_selector` / `networkidle`、移除 debug 寫檔、`delay` 預設 0.5s、共用 DB 連線、WAL mode | ~1 小時 | 11× | 低 |
| **B** 並發 | A + `asyncio.Semaphore(5–8)` 多 context 並發、DB 寫入 lock/queue | ~10–15 分鐘 | 44× | 中 |
| **C** HTTP 直連 | 逆向 NHI/TFDA 表單 POST，改 `httpx.AsyncClient` + `lxml`/`selectolax` | ~3–5 分鐘 | 130× | 中高 |
| **D** OpenData ETL | 改抓 TFDA / 健保署開放資料 CSV，pandas UPSERT；爬蟲降級為「只補圖片/缺漏」維運工具 | ~1 分鐘 + 補圖 | 600×+ | 中（需確認資料欄位對應）|

**檔案異動範圍**：
- `scripts/nhi_crawler.py`：抽離 browser/context 管理、改顯式等待
- `scripts/batch_update.py`：改 async worker pool、DB 連線共用、`PRAGMA journal_mode=WAL`
- `scripts/opendata_importer.py`（新增）：方案 D 的 CSV ETL 任務
- `admin_routes.py`：批次更新 API 補充並發/延遲參數

**新增/修改端點**：
```
POST /admin/api/batch-update/start         (補充參數：concurrency、mode=crawler/opendata)
GET  /admin/api/batch-update/status        (現有，補充 throughput 指標)
POST /admin/api/opendata/sync              (方案 D 新增：手動觸發 OpenData 同步)
```

**預定資料來源（方案 D 候選）**：
- TFDA 西藥許可證 OpenData：<https://data.gov.tw/dataset/40402>
- 健保用藥品項 OpenData：<https://data.gov.tw/dataset/24074>
- 衛福部藥局名冊（同步用於 Feature 03）：<https://data.gov.tw/dataset/6122>

**排程整合**：
- 完成方案 D 後，由 `APScheduler` 每週自動執行一次 OpenData 同步
- 爬蟲改為「按需補缺」：僅針對 OpenData 無提供的欄位（如仿單圖片）執行

**驗收條件**：
- [ ] 方案 A 完成：全表更新 ≤ 1.5 小時
- [ ] 方案 B 完成：全表更新 ≤ 20 分鐘
- [ ] 方案 D 完成：OpenData 同步 ≤ 3 分鐘，覆蓋率 ≥ 90%
- [ ] 後台 `/admin` 儀表板可顯示更新進度與 throughput（筆/分鐘）

---

## Feature 01：個人用藥管理

### 1.1 藥品提醒系統

**新增資料表**：
```sql
medications (
  id, profile_id, drug_id, drug_name_custom,
  dosage, dosage_unit, route,           -- 劑量、單位、用法
  frequency_type, frequency_detail,     -- daily/weekly/custom
  meal_timing,                          -- before/after/with/anytime
  start_date, end_date,
  current_stock, stock_unit,            -- 庫存（for 補藥提醒）
  source,                               -- manual/ocr/prescription
  is_active, created_at
)

medication_schedules (
  id, medication_id,
  time_of_day,                          -- HH:MM
  days_of_week                          -- JSON [0-6] or null for daily
)

push_tokens (
  id, user_id, platform, token, created_at
)
```

**新增端點**：
```
GET    /api/user/medications
POST   /api/user/medications
PUT    /api/user/medications/<id>
DELETE /api/user/medications/<id>
POST   /api/user/medications/<id>/schedules
DELETE /api/user/medications/<id>/schedules/<schedule_id>
POST   /api/user/push-token              (註冊推播 token)
```

**推播服務**：
- 使用 `APNs`（iOS）/ `FCM`（Android）
- 排程任務（建議 APScheduler 或 Celery）定期掃描 `medication_schedules`，觸發推播
- 推播 payload 含 `medication_id`，前端收到後 deep link 到服藥確認頁

### 1.2 服藥記錄追蹤

**新增資料表**：
```sql
adherence_logs (
  id, medication_id, schedule_id, profile_id,
  scheduled_at,                         -- 原定服藥時間
  taken_at,                             -- 實際服藥時間（null = 未服）
  status,                               -- taken/skipped/delayed/missed
  notes,
  stock_after                           -- 服藥後剩餘庫存
)
```

**新增端點**：
```
GET  /api/user/adherence?profile_id=&from=&to=    (日曆視圖資料)
POST /api/user/adherence                          (新增一筆紀錄)
PUT  /api/user/adherence/<id>                     (修改紀錄)
GET  /api/user/adherence/stats?profile_id=&days=  (順從率統計)
```

### 1.3 處方箋 OCR 匯入

**修改現有**：
- 現有 `/api/recognize` 用於藥品圖片辨識
- 新增獨立端點處理**處方箋**（不同 prompt、不同解析結構）

**新增資料表**：
```sql
prescriptions (
  id, profile_id,
  image_path,                           -- 加密或僅本地不上傳
  ocr_result,                           -- JSON 原始解析結果
  hospital, doctor, issued_date,
  status,                               -- draft/confirmed
  created_at
)
```

**新增端點**：
```
POST /api/user/prescriptions/ocr        (上傳處方箋 → OCR → 回傳草稿)
POST /api/user/prescriptions/confirm    (確認草稿 → 寫入 medications)
GET  /api/user/prescriptions
```

**Vision API 修改**：
- 新增 `recognize_prescription()` 方法，使用不同 system prompt
- 解析欄位：藥名、劑量、頻率、天數、用法、開立日期、醫師、院所

**⚠️ 重要**：處方箋影像屬敏感個資，**建議不上傳雲端**，僅本地解析後丟棄原圖，或加密存放。

### 1.4 用藥歷史匯出 PDF

**技術選型**：
- 建議使用 `reportlab`（輕量）或 `WeasyPrint`（HTML → PDF）
- 在後端產生 PDF 回傳檔案流（不存檔）

**新增端點**：
```
GET /api/user/medications/export-pdf?profile_id=&from=&to=&lang=
```

**限制**：付費功能，需先通過訂閱驗證中介層

---

## Feature 02：線上藥師諮詢

### 2.1 AI 藥師對話

**修改現有**：
- 現有 Vision API 已有 Claude 整合，擴充為「對話模式」

**新增資料表**：
```sql
consultations (
  id, profile_id, type,                 -- ai/human
  status,                               -- active/ended/pending_human
  started_at, ended_at
)

consultation_messages (
  id, consultation_id,
  sender_type,                          -- user/ai/pharmacist
  sender_id,
  content_type,                         -- text/image
  content,
  image_path,
  created_at
)
```

**新增端點**：
```
POST /api/user/consultations                      (開始新諮詢)
GET  /api/user/consultations                      (歷史紀錄)
GET  /api/user/consultations/<id>/messages
POST /api/user/consultations/<id>/messages        (發送訊息)
POST /api/user/consultations/<id>/request-human   (轉真人)
POST /api/user/consultations/<id>/end
```

**AI 對話邏輯**：
- System Prompt 定義「藥師人格」+ 免責聲明
- 維護 per-consultation 的 message history（context window 管理）
- 信心度低 / 高風險問題 → 自動觸發轉真人邏輯
- 若使用者有授權，可引用 `medications` 資料提供個人化回覆

### 2.2 真人藥師預約（Phase 2）

> ⚠️ 需先完成藥師合作 B 端設計，Phase 2 實作

**資料表預留**：
```sql
pharmacists (id, name, license_no, specialty, bio, avatar)
pharmacist_schedules (pharmacist_id, date, time_slot, is_available)
appointments (
  id, profile_id, pharmacist_id, consultation_id,
  date, time_slot, duration_min,
  status,                               -- pending/confirmed/cancelled/done
  payment_id, amount
)
```

---

## Feature 03：智慧化功能

### 3.1 藥局地圖

**資料來源整合**：
- 衛福部開放資料（https://data.gov.tw/dataset/6122）定期同步
- Google Places API 補充資料

**新增資料表**：
```sql
pharmacies (
  id, name, address, lat, lng,
  phone, hours,                         -- JSON
  is_24h, is_nhi_contracted,
  data_source, updated_at
)

user_favorite_pharmacies (user_id, pharmacy_id)
```

**新增端點**：
```
GET /api/pharmacies?lat=&lng=&radius=&filter=      (附近藥局)
GET /api/pharmacies/<id>
POST /api/user/favorite-pharmacies/<pharmacy_id>
DELETE /api/user/favorite-pharmacies/<pharmacy_id>
```

**後台排程**：
- 每週同步衛福部開放資料到 `pharmacies` 表

### 3.2 補藥提醒

**邏輯整合至現有 medications 排程**：
- 每日任務掃描 `medications.current_stock` 和每日用量
- 計算剩餘天數，≤ N 天時發推播
- 推播內容含最近藥局 deep link（接 3.1 資料）

**新增端點**：
```
PUT /api/user/medications/<id>/stock    (手動更新庫存)
```

---

## Feature 04：社群與教育（知識卡片）

**新增資料表**：
```sql
knowledge_cards (
  id, title, summary, content,
  category, tags,                       -- JSON
  related_drug_ids,                     -- JSON
  source, reviewed_by, reviewed_at,
  published_at, status,                 -- draft/review/published
  view_count, favorite_count
)

user_card_interactions (
  user_id, card_id,
  action,                               -- view/favorite/share
  created_at
)
```

**新增端點**：
```
GET  /api/knowledge-cards?category=&tag=&q=&page=  (公開，無需登入)
GET  /api/knowledge-cards/<id>
GET  /api/user/knowledge-cards/favorites
POST /api/user/knowledge-cards/<id>/favorite
DEL  /api/user/knowledge-cards/<id>/favorite

# 後台（admin）
POST   /admin/api/knowledge-cards
PUT    /admin/api/knowledge-cards/<id>
POST   /admin/api/knowledge-cards/<id>/review   (審核)
POST   /admin/api/knowledge-cards/<id>/publish
DELETE /admin/api/knowledge-cards/<id>
```

**推播整合**：
- 每日推播任務：依使用者用藥標籤推送相關卡片

---

## Feature 06：安全性功能

> ⭐ 架構核心，需優先建立，其他 Feature 依賴此模組

### 6.1 成分資料表

**新增資料表**：
```sql
drug_ingredients (
  id, drug_id, ingredient_id,
  amount, unit, is_active_ingredient
)

ingredients (
  id, name_zh, name_en,
  cas_number,                           -- 化學唯一識別碼
  atc_code                              -- WHO ATC 分類
)
```

### 6.2 交互作用資料庫

```sql
drug_interactions (
  id, ingredient_a_id, ingredient_b_id,
  severity,                             -- contraindicated/major/moderate/minor
  description_zh, description_en,
  mechanism_zh,                         -- 付費功能
  recommendation_zh,
  source_reference,
  updated_at
)
```

### 6.3 使用者過敏資料

```sql
user_allergies (
  id, profile_id,
  ingredient_id,                        -- 外鍵到 ingredients
  free_text_name,                       -- 若 ingredients 無此成分
  severity,                             -- mild/moderate/severe
  reaction_description,
  verified_by,                          -- self/doctor/ocr
  created_at
)
```

### 6.4 用藥安全分級

```sql
drug_safety_profiles (
  id, drug_id,
  pregnancy_category,                   -- A/B/C/D/X
  lactation_risk,                       -- L1-L5
  pediatric_notes,
  geriatric_beers_criteria,             -- boolean + reason
  hepatic_adjustment, renal_adjustment,
  source_reference, updated_at
)
```

### 6.5 安全檢查 API

**新增端點**：
```
POST /api/safety/check                  (主動安全檢查，帶藥品清單)
GET  /api/safety/interactions?drug_ids= (查詢特定藥品組合)
GET  /api/user/safety/profile-check     (對現有用藥清單全掃描)
```

**安全檢查邏輯（後端服務）**：
- `SafetyCheckService.check_all(profile_id, new_drug_id)` → 依序執行：
  1. 過敏比對
  2. 重複用藥比對
  3. 交互作用查詢（免費：contraindicated + major；付費：全部）
  4. 安全分級（依 profile 屬性）
- 結果寫入 `safety_check_logs` 供稽核
- 回傳格式統一：`{ alerts: [{ level, type, message, recommendation }] }`

```sql
safety_check_logs (
  id, profile_id, drug_id, triggered_at,
  check_type, result_level,             -- ok/minor/moderate/major/contraindicated
  user_action,                          -- acknowledged/ignored/consulted
  context                               -- JSON（諮詢 ID / 用藥清單快照）
)
```

---

## 現有 API 修改清單

| 端點 | 修改內容 |
|---|---|
| `POST /api/recognize` | 加入可選 JWT；登入用戶記錄辨識歷史；計入每日額度；辨識後觸發安全檢查（若 profile_id 帶入）|
| `GET /api/drug/<id>` | 補充回傳：成分清單、安全分級、交互作用摘要（高危等級）|
| `POST /api/search` | 回傳補充：是否與使用者現有用藥有警示 |
| `/admin/api/dashboard` | 補充統計：用戶數、訂閱數、諮詢數、知識卡片數 |

---

## 資料庫遷移建議

| 項目 | 現狀 | 建議 |
|---|---|---|
| 資料庫 | SQLite | 短期可維持；中長期遷移 PostgreSQL（並發/複雜查詢）|
| ORM | 原生 sqlite3 | 建議引入 SQLAlchemy（減少手寫 SQL、支援 Migration）|
| Migration | 無 | 導入 Alembic（版本化資料庫變更）|
| 連線管理 | 每次 `sqlite3.connect()` | 使用 connection pool（SQLAlchemy 內建）|
| 密碼雜湊 | 無 | bcrypt |
| 敏感欄位 | 明文 | AES-256 加密（處方箋影像路徑、過敏紀錄）|

---

## 新增套件建議

```
# 身份驗證
flask-jwt-extended       # JWT
bcrypt                   # 密碼雜湊
authlib                  # OAuth (Apple/Google)

# 資料庫
flask-sqlalchemy         # ORM
alembic                  # Migration
psycopg2-binary          # PostgreSQL adapter（未來遷移用）

# 排程任務
apscheduler              # 推播/補藥提醒排程

# 推播通知
firebase-admin           # FCM (Android)
# APNs 使用 requests 直接呼叫或 aioapns

# PDF 匯出
reportlab                # 或 WeasyPrint

# WebSocket（諮詢即時對話）
flask-socketio           # 或遷移 FastAPI + WebSocket

# 驗證/序列化
marshmallow              # 請求資料驗證

# 爬蟲優化（A-3）
httpx                    # 異步 HTTP（方案 C/D）
selectolax               # 高速 HTML 解析（替代 BeautifulSoup）
pandas                   # OpenData CSV ETL（方案 D）
```

---

## 優先開發順序建議

```
Phase 0（前置架構）：
  A-1 使用者帳號系統 + JWT
  A-2 訂閱/額度管理
  A-3 爬蟲方案 A（Quick Win）：移除硬等待、Browser 重用、WAL
  資料庫：SQLAlchemy + Alembic 導入

Phase 1（MVP 核心）：
  A-3 爬蟲方案 B（並發）+ 方案 D（OpenData ETL）
  Spec 06  安全性功能資料表 + SafetyCheckService
  Spec 01  medications / schedules / adherence_logs
           處方箋 OCR（新 prompt）
           推播排程（APScheduler + FCM/APNs）
  Spec 03  藥局地圖（pharmacy 資料同步）
           補藥提醒（整合推播）

Phase 2：
  Spec 02  AI 藥師對話
           真人藥師預約
  Spec 04  知識卡片 CRUD + 審核流程
           個人化推送
  PDF 匯出

Phase 3：
  健保快易通 API 串接
  庫存/比價（待合作）
  WebSocket 即時諮詢升級
```

---

## 安全性與法規要求

| 項目 | 要求 |
|---|---|
| 個資加密 | 用藥、過敏、處方箋等敏感欄位需加密存放（AES-256）|
| 傳輸安全 | 全 HTTPS；JWT 短效（15min）+ Refresh Token（7天）|
| 稽核日誌 | 安全警示觸發紀錄需保存 ≥ 1 年 |
| 個資刪除 | 支援使用者「刪除帳號」（PDPA 符合性），級聯刪除所有個人資料 |
| API 限流 | 所有公開端點需 Rate Limiting（防爬蟲 / DDoS）|
| 處方箋影像 | 建議不上傳雲端，本地解析後丟棄；若上傳需獨立加密 bucket |

---

## 未決議題（需後端開發者決策）

- [ ] SQLite → PostgreSQL 遷移時間點（用戶量多少開始遷移？）
- [ ] 排程任務採用 APScheduler（單機）還是 Celery + Redis（多機擴展）？
- [ ] WebSocket 即時對話採用 Flask-SocketIO 還是另開 FastAPI 服務？
- [ ] FCM/APNs 推播是否需要佇列（高並發時）？
- [ ] 交互作用資料庫採購哪個商業資料庫（DrugBank API？授權費用？）？
- [ ] 是否統一使用 Blueprint 拆分各模組（medications、safety、consultation…）？
- [ ] 爬蟲優化（A-3）採方案 B（並發 Playwright）或方案 C（HTTP 逆向）作為短期主力？
- [ ] OpenData（方案 D）欄位對應到 `drugs` 表的差異需要對齊（CAS、ATC 是否齊全）？
