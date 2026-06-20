# 📘 藥知道 — 後端文件

Flask 後端：API 路由、AI Provider 策略、管理員後台、Docker、環境變數。

> 前端請見 [README.frontend.md](README.frontend.md)。  
> iOS App 請見 [README.app.md](README.app.md)。

---

## 🗂️ 後端結構

```
MUS_Project_v2/
├── main.py                    # Flask 入口（含 blueprint 註冊、scheduler 啟動）
├── config.py                  # 配置管理（依 FLASK_ENV 切換 Dev/Prod）
├── admin_routes.py            # 管理員後台 API 藍圖
├── drug_database.py           # 藥物資料庫查詢模組
├── drug_recognition.db        # SQLite 資料庫
│
├── vision_api_gemini.py       # Gemini Vision API（預設主 provider）
├── vision_api_openai.py       # OpenAI Vision（備援）
├── vision_api_google.py       # Google Vision API
├── vision_api_claude.py       # Claude Vision API
│
├── routes/                    # 使用者端 API blueprint
│   ├── auth.py                # 註冊 / 登入 / Profile
│   ├── medications.py         # 用藥清單、服藥紀錄
│   ├── safety.py              # 安全檢查（過敏 / 交互作用）
│   └── consult.py             # AI 諮詢
│
├── services/                  # 共用服務層
│   ├── system_log.py          # 應用程式日誌 → SQLite（供後台查詢）
│   ├── scheduler.py           # APScheduler（用藥提醒、庫存檢查）
│   ├── push_service.py        # 推播
│   └── ai/
│       ├── recognizer_router.py  # 影像辨識主備切換 router
│       ├── consult_client.py     # AI 諮詢 client（OpenAI 相容）
│       ├── usage_log.py          # AI Provider 用量背景批次寫入
│       └── errors.py             # 例外分類（quota / retryable / fatal）
│
├── models/                    # SQLAlchemy ORM 模型
├── scripts/                   # 工具腳本（爬蟲、批次更新、debug）
├── tests/                     # pytest 測試
│
├── Dockerfile, docker-compose.yml, nginx.conf
└── requirements.txt
```

---

## ⚙️ 安裝

### 前置要求

- Python 3.10+
- pip
- 至少一組 AI API Key（推薦 Gemini）

### 步驟

```powershell
# Windows PowerShell
git clone https://github.com/sunmin-oss/MUS_Project_v2.git
cd MUS_Project_v2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env   # 填入 GEMINI_API_KEY 等
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

> ⚠️ **每次切換到新的虛擬環境後都要重裝依賴**，否則會出現 `ModuleNotFoundError: No module named 'bcrypt'`。

---

## 🚀 啟動

### 開發環境

```powershell
$env:PORT="5001"; python main.py    # Windows
```

```bash
PORT=5001 python main.py            # macOS / Linux
```

- 預設啟動於 `http://127.0.0.1:5001`（同時監聽區網 IP）
- 停止：`Ctrl+C`
- Port 被佔用可改 `$env:PORT="5002"`

### 生產環境

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 main:app
```

---

## 🐳 Docker 部署

```bash
docker compose up -d
```

`docker-compose.yml` 同時啟動 Flask app + nginx 反向代理（見 `nginx.conf`）。

---

## 📡 API 概覽

| 分類 | 方法 | 路徑 | 說明 |
|------|------|------|------|
| 系統 | GET | `/api/health` | 健康檢查 |
| 辨識 | POST | `/api/recognize` | 單顆藥物拍照辨識 |
| 辨識 | POST | `/api/recognize_prescription` | 整張藥單 OCR + 比對 |
| 搜尋 | POST | `/api/search` | 名稱 / 許可證搜尋 |
| 藥物 | GET | `/api/drug/<id>` | 藥物詳細資料 |
| 認證 | POST | `/api/auth/register` `/login` | JWT 註冊 / 登入 |
| 認證 | GET | `/api/auth/profiles` | 取得家人 profile |
| 用藥 | GET/POST | `/api/user/medications` | 個人用藥清單 |
| 服藥 | GET/POST | `/api/user/adherence` | 服藥紀錄 |
| 安全 | POST | `/api/safety/check` | 過敏 / 交互作用檢查 |
| 諮詢 | POST | `/api/consult` | AI 用藥諮詢 |
| 後台 | GET | `/admin/api/dashboard` | 後台儀表板 |
| 後台 | GET | `/admin/api/logs/categories` | Log 類別 + 筆數 |
| 後台 | GET | `/admin/api/logs/query?category=...` | 統一 Log 查詢 |
| 後台 | GET | `/admin/api/ai-usage` `/ai-logs` | AI Provider 用量分析 |

詳細欄位請見 `admin_routes.py`、`routes/` 各檔案。

### 範例：辨識 API 回應

```json
{
  "success": true,
  "request_id": "uuid",
  "recognized_items": [
    {
      "name": "普拿疼",
      "confidence": 0.92,
      "drug_id": 123,
      "details": {
        "chinese_name": "普拿疼",
        "english_name": "Paracetamol",
        "license_number": "衛部藥製字第000123號",
        "shape": "圓形",
        "color": "白色",
        "usage": "退燒、止痛"
      }
    }
  ]
}
```

---

## 🛠 管理員後台 API

進入 `http://127.0.0.1:5001/admin` 後可使用：

1. **儀表板** — 藥物 / 圖片 / 快取 / 上傳統計
2. **藥物管理** — CRUD、圖片上傳
3. **使用者** — 帳號 / Profile 管理
4. **NHI 快取** — 健保署藥品資料快取維護
5. **上傳檔案** — 暫存清理
6. **設定** — 系統設定、舊版日誌檢視
7. **API 統計** — 端點呼叫量、Top 搜尋字
8. **AI 使用** — 依 provider / model 分項統計
9. **📋 Log 紀錄** — 統一查詢五大類 log：
   - 應用程式日誌（INFO/WARNING/ERROR）
   - API 請求
   - AI Provider 呼叫
   - 服藥紀錄
   - 安全檢查
   - 支援關鍵字、時間範圍、類別專屬篩選（等級 / 狀態碼 / Method / 功能 / User ID）
10. **批次更新** — 從健保署 / TFDA 批次爬取藥物資料

---

## 🔌 AI Provider 策略

### 影像辨識（recognize / recognize_prescription）

```
Gemini 主 key
   ↓ (quota / retryable)
Gemini 備用 key（GEMINI_BACKUP_API_KEY）
   ↓
OpenAI Fallback（OPENAI_FALLBACK_*，預設關閉）
```

由 `services/ai/recognizer_router.py` 控制；每次切換、失敗都會寫入 `ai_provider_logs`，後台「AI 使用」與「Log 紀錄」皆可查。

### AI 諮詢（consult）

使用 `OPENAI_CONSULT_*` 設定，預設指向 Groq 免費層（`llama-3.3-70b-versatile`）。  
要改用 OpenAI：把 `OPENAI_CONSULT_BASE_URL` 改成 `https://api.openai.com/v1`、`OPENAI_CONSULT_MODEL` 改為 `gpt-4o-mini`。

---

## 🛠️ 環境變數總表

| 變數名 | 說明 | 預設值 |
|------|------|--------|
| `FLASK_ENV` | development / production | development |
| `PORT` | 伺服器埠號 | 5000 |
| `API_PROVIDER` | gemini / google / claude | gemini |
| `GEMINI_API_KEY` | Gemini 主 key | - |
| `GEMINI_BACKUP_API_KEY` | Gemini 備用 key | - |
| `OPENAI_FALLBACK_API_KEY` | OpenAI 相容備援 | - |
| `OPENAI_CONSULT_API_KEY` | 諮詢用 key（預設 Groq） | - |
| `OPENAI_CONSULT_MODEL` | 諮詢模型 | llama-3.3-70b-versatile |
| `OPENAI_CONSULT_BASE_URL` | 諮詢 API base url | https://api.groq.com/openai/v1 |
| `AI_FALLBACK_ENABLED` | 啟用主備切換 | true |
| `AI_FALLBACK_COOLDOWN_SEC` | 主 provider 冷卻秒數 | 300 |
| `AI_FALLBACK_FAIL_THRESHOLD` | 連續失敗幾次觸發 fallback | 3 |
| `AI_TIMEOUT_SEC` | AI 請求逾時 | 20 |
| `AI_CONSULT_MAX_TOKENS` | 諮詢回應上限 | 800 |
| `AI_CONSULT_RATE_PER_MIN` | 諮詢速率上限 | 20 |
| `JWT_SECRET_KEY` | JWT 簽章密鑰 | 自動產生（dev） |
| `DATABASE_PATH` | SQLite 路徑 | drug_recognition.db |
| `UPLOAD_FOLDER` | 上傳目錄 | uploads |
| `MAX_FILE_SIZE` | 上傳上限（bytes） | 10485760 |
| `MIN_CONFIDENCE` | 辨識信心度閾值 | 0.3 |
| `MAX_RESULTS` | 最多回傳結果數 | 5 |
| `LOG_LEVEL` | 日誌等級 | INFO |

---

## 🔧 開發指令

```bash
# 跑測試
pytest

# 啟動爬蟲（單藥）
python scripts/nhi_crawler.py --license <許可證號>

# 批次更新藥物資料
python scripts/batch_update.py

# 檢查資料庫
python scripts/check_db.py

# 壓測（需安裝 locust）
locust -f locustfile.py --host http://127.0.0.1:5001
```

---

## 🐛 常見問題

### Q: 啟動報 `ModuleNotFoundError: No module named 'bcrypt'`
**A:** 你切到了某個虛擬環境（如 `.venv`），但裡面沒裝依賴：
```powershell
pip install -r requirements.txt
```
或退出 venv 用系統 Python：`deactivate`。

### Q: Port 5000 被佔用
**A:** 改用 5001：`$env:PORT="5001"; python main.py`。若還是被佔，可在 PowerShell 找出 PID：
```powershell
netstat -ano | Select-String ':5000 '
```

### Q: Gemini 回 429 RESOURCE_EXHAUSTED
**A:** 免費層每日 20 次。系統會自動切到 `GEMINI_BACKUP_API_KEY`；若沒設定備用 key，可等隔日重置或填入 OpenAI fallback。

### Q: 後台 Log 紀錄頁是空的
**A:** `system_logs` 表會在首次啟動由 `services/system_log.install()` 自動建立並開始背景批次寫入；至少要重啟一次伺服器才會有資料。

---

## 🤝 Git 規範

完整規範請看 [CONTRIBUTING.md](CONTRIBUTING.md)。重點：

- **禁止**直接在 `main` 上 commit / push
- 功能：`feature/<描述>` → merge 回 `develop`
- 修復：`fix/<描述>` → merge 回 `develop`
- 緊急：`hotfix/<描述>` → merge 回 `main` 與 `develop`
- 發布：`release/v版號` → merge 至 `main`（打 Tag）再同步 `develop`
- Commit 格式：`<type>(<scope>): <中文描述>`（Conventional Commits）
