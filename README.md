# 藥知道 - 藥物辨識系統 v1.0.0

## 📋 專題簡介

**藥知道** 是一個針對年長者設計的**藥物辨識系統**，透過 **Google Gemini API**、**Google Vision API** 或 **Claude Vision API** 進行藥物影像識別，提供簡潔友好的使用介面。

### 🎯 核心特性

- ✅ **多 API 支援** - 預設使用 Gemini API（推薦），亦支援 Google Vision 與 Claude Vision
- ✅ **年長者友好** - 大字體、高對比度、簡單按鈕、少於 4 個選項
- ✅ **快速部署** - 輕量級設計，支援 Docker 一鍵部署
- ✅ **多種識別方式** - 支援圖片拍照、上傳辨識和名稱搜尋
- ✅ **完整藥物資訊** - 自動查詢中英文名稱、許可證、成分、用途等

---

## 🗂️ 專案結構

```
MUS_Project_v2/
├── main.py                    # Flask 後端主程式
├── config.py                  # 配置管理
├── admin_routes.py            # 管理員後台路由
├── drug_database.py           # 藥物資料庫查詢模組
├── vision_api_gemini.py       # Gemini Vision API（預設）
├── vision_api_google.py       # Google Vision API
├── vision_api_claude.py       # Claude Vision API
├── index.html                 # 前端首頁（年長者友好設計）
├── admin.html                 # 管理員後台頁面
├── drug_recognition.db        # SQLite 藥物資料庫
├── requirements.txt           # Python 依賴列表
├── .env.example               # 環境變數範例
├── Dockerfile                 # Docker 構建檔案
├── docker-compose.yml         # Docker Compose 配置
├── CONTRIBUTING.md            # 貢獻指南與 Git 規範
├── README.md                  # 本文件
├── docs/                      # 文件
│   ├── ARCHITECTURE.md        # 系統架構說明
│   ├── DESIGN.md              # 設計文件
│   └── QUICKSTART.md          # 快速入門指南
├── tests/                     # 測試檔案
├── scripts/                   # 工具腳本（爬蟲、批次更新等）
├── debug/                     # 除錯用暫存檔
├── medicine_photos/           # 藥物圖片
└── uploads/                   # 上傳暫存目錄
```

---

## ⚙️ 安裝與配置

### 前置要求

- Python 3.8+
- pip (Python 套件管理器)
- Google Cloud Vision API 密鑰 **或** Claude API 密鑰

### 1️⃣ 克隆專案

```bash
git clone https://github.com/sunmin-oss/MUS_Project_v2.git
cd MUS_Project_v2
```

### 2️⃣ 安裝依賴

```bash
# 使用 pip 安裝
pip install -r requirements.txt

# 或使用虛擬環境（推薦）
python -m venv venv

# 激活虛擬環境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 然後安裝依賴
pip install -r requirements.txt
```

### 3️⃣ 配置 API 密鑰

複製 `.env.example` 為 `.env` 並填入您的 API 密鑰：

```bash
cp .env.example .env
```

編輯 `.env` 檔案：

```bash
# API 提供商選擇 ('gemini', 'google' 或 'claude')
API_PROVIDER=gemini

# Google Gemini API（推薦）
# 取得方式: https://aistudio.google.com/ → Get API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud Vision API（備選）
GOOGLE_VISION_API_KEY=your_google_vision_api_key_here

# Claude Vision API（備選）
CLAUDE_API_KEY=your_claude_api_key_here
```

### 4️⃣ 藥物資料庫

專案已內建 `drug_recognition.db` 資料庫，無需額外設定。

---

## 🚀 運行系統

### 開發環境

```bash
# 確保激活了虛擬環境
python main.py
```

系統將在 `http://localhost:5000` 啟動。

### 生產環境

使用 Gunicorn（推薦）：

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

---

## 🐳 使用 Docker 部署（可選）

### 構建 Docker 映像

```bash
docker build -t mus2:latest .
```

### 運行 Docker 容器

```bash
docker run -p 5000:5000 \
  -e GOOGLE_VISION_API_KEY=your_key_here \
  -e API_PROVIDER=google \
  mus2:latest
```

### 使用 Docker Compose

```bash
# 編輯 docker-compose.yml 填入 API 密鑰
docker-compose up
```

---

## 📡 API 文件

### 健康檢查

```http
GET /api/health
```

**回應:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-27T10:00:00",
  "services": {
    "vision_api": "ready",
    "database": "ready"
  }
}
```

### 藥物辨識（拍照上傳）

```http
POST /api/recognize
Content-Type: multipart/form-data

image: <binary image file>
language: zh (可選)
```

**成功回應:**
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
  ],
  "message": "辨識完成，找到 3 個匹配結果"
}
```

### 藥物搜尋

```http
POST /api/search
Content-Type: application/json

{
  "query": "普拿疼",
  "limit": 10
}
```

### 取得藥物詳細資訊

```http
GET /api/drug/{drug_id}
```

---

## 🎨 前端設計特點

### 為年長者優化的設計

1. **大字體** (18px+) - 易於閱讀
2. **高對比度** - 深紫色背景配白色文字
3. **簡單按鈕** - 每個頁面最多 2-3 個選項
4. **清晰流程** - 主頁 → 拍照 / 搜尋 → 結果 → 詳情
5. **觸摸友好** - 大號按鈕，易於點擊
6. **直觀圖標** - 使用 emoji 提示功能

### 用戶流程

```
[首頁] 
  ├─ [拍照辨識] → 選擇/拍照 → 上傳 → [辨識結果] → [藥物詳情]
  └─ [搜尋藥物] → 輸入名稱 → [搜尋結果] → [藥物詳情]
```

---

## 🔌 API 提供商選擇

### Google Gemini API（推薦）

- 使用模型：`gemini-2.5-flash`
- 免費額度充足，辨識能力強
- 設置：前往 [Google AI Studio](https://aistudio.google.com/) → Get API Key

### Google Cloud Vision API

- 功能完整（標籤識別、文字識別、物體偵測）
- 設置：前往 [Google Cloud Console](https://console.cloud.google.com/) → 啟用 Vision API

### Claude Vision API

- 更智能的醫學術語理解能力
- 設置：前往 [Anthropic](https://www.anthropic.com/) → 獲取 API 密鑰

---

## 📱 測試系統

### 使用瀏覽器
1. 打開 `http://localhost:5000`
2. 點擊「拍照辨識藥物」
3. 上傳或拍照
4. 查看識別結果

### 使用 cURL 測試

```bash
# 測試 API 健康狀態
curl http://localhost:5000/api/health

# 搜尋藥物
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"普拿疼","limit":5}'
```

---

## 🛠️ 環境變數說明

| 變數名 | 說明 | 預設值 | 必需 |
|------|------|--------|-----|
| `API_PROVIDER` | API 提供商 ('gemini', 'google' 或 'claude') | gemini | ✅ |
| `GEMINI_API_KEY` | Google Gemini API 密鑰 | - | 若使用 Gemini |
| `GOOGLE_VISION_API_KEY` | Google Vision API 密鑰 | - | 若使用 Google |
| `CLAUDE_API_KEY` | Claude API 密鑰 | - | 若使用 Claude |
| `FLASK_ENV` | Flask 環境 (development/production) | development | ❌ |
| `FLASK_DEBUG` | 除錯模式 | False | ❌ |
| `DATABASE_PATH` | 藥物資料庫路徑 | drug_recognition.db | ❌ |
| `UPLOAD_FOLDER` | 上傳檔案目錄 | uploads | ❌ |
| `MAX_FILE_SIZE` | 最大上傳檔案大小（位元組） | 10485760 (10MB) | ❌ |
| `MIN_CONFIDENCE` | 識別信心度閾值 | 0.3 | ❌ |
| `MAX_RESULTS` | 最多回傳結果數 | 5 | ❌ |
| `LOG_LEVEL` | 日誌等級 | INFO | ❌ |

---

## 🐛 常見問題與排除

### Q: API 密鑰無法驗證？
**A:** 
1. 確認 `.env` 檔案已建立
2. 檢查 API 密鑰是否正確複製
3. 確認未包含執行空格

### Q: 上傳圖片後顯示"未能識別"？
**A:**
1. 確保光線充足
2. 藥物清晰置中
3. 嘗試不同角度拍照
4. 檢查圖片格式是否支持（JPG, PNG）

### Q: 搜尋功能無法使用？
**A:**
1. 檢查 `drug_recognition.db` 是否存在
2. 確認資料庫位置正確
3. 查看服務器日誌了解詳細錯誤

### Q: 如何自訂資料庫？
**A:**
建立空資料庫：
```python
import sqlite3
conn = sqlite3.connect('drug_recognition.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE drugs (
        drug_id INTEGER PRIMARY KEY,
        chinese_name TEXT,
        english_name TEXT,
        license_number TEXT,
        shape TEXT,
        color TEXT,
        usage TEXT,
        formulation TEXT,
        dosage_strength TEXT
    )
''')
conn.commit()
conn.close()
```

---

## 🚀 性能優化建議

### 後端優化
- 使用 Redis 快取 API 回應
- 實現知識圖譜（圖片 → 藥物 ID 的直接映射）
- 批量 API 呼叫以減少延遲

### 前端優化
- 圖片壓縮在上傳前
- 實現離線快取
- 本地儲存最近查詢

### 部署優化
- 使用 CDN 加速靜態資源
- 設置反向代理（nginx）
- 定期更新資料庫

---

## 📚 相關資源

- [Google Vision API 文件](https://cloud.google.com/vision/docs)
- [Claude API 文件](https://docs.anthropic.com/)
- [Flask 官方文件](https://flask.palletsprojects.com/)
- [Docker 文件](https://docs.docker.com/)

---

## 📝 授權與免責聲明

此系統僅供教育和參考用途。使用者在購買、服用或停用任何藥物前，**務必諮詢您的醫生或藥師**。

開發者不對因使用此系統而引起的任何後果負責。

---

## 👥 貢獻者

- 藥知道開發團隊

協作規範請參閱 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📧 聯絡與支持

如有問題或建議，請聯絡開發團隊。

**版本：** v1.0.0  
**更新日期：** 2026 年 5 月 19 日
