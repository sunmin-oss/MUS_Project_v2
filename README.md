# 藥知道 - 智慧用藥管理系統 v2

針對年長者設計的**藥物辨識 + 用藥管理**系統。整合多家 AI Vision／LLM、JWT 帳號、後台管理與 iOS App。

## 🔗 文件導覽

| 文件 | 內容 |
|------|------|
| 📘 [README.backend.md](README.backend.md) | Flask 後端、API、AI Provider、後台、Docker、環境變數 |
| 📗 [README.frontend.md](README.frontend.md) | Web 前端（index.html / admin.html）、Capacitor iOS App |
| 🤝 [CONTRIBUTING.md](CONTRIBUTING.md) | Git 分支規範、Commit message 格式 |
| 🏗 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 系統架構 |
| 🎨 [docs/DESIGN.md](docs/DESIGN.md) | UI/UX 設計 |
| ⚡ [docs/QUICKSTART.md](docs/QUICKSTART.md) | 快速入門 |

## ✨ 核心特性

- 📷 拍照辨識單顆藥物與整張藥單（OCR）
- 💊 個人用藥清單、服藥提醒、服藥紀錄（adherence）
- ⚠️ 過敏／交互作用安全檢查
- 💬 AI 用藥諮詢（Groq / OpenAI 相容介面）
- 🛠 管理員後台（藥物 CRUD、批次更新、AI Provider 監控、**統一 Log 紀錄查詢**）
- 📱 iOS App（Capacitor 8）
- 🔒 JWT 認證 + 多 Profile（一帳號管理多位家人）

## 🚀 30 秒上手

```powershell
# 1. 安裝
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. 設定（複製 .env.example → .env，填 GEMINI_API_KEY）
cp .env.example .env

# 3. 啟動
$env:PORT="5001"; python main.py
```

開瀏覽器：
- 前端首頁：<http://127.0.0.1:5001/>
- 管理後台：<http://127.0.0.1:5001/admin>
- 健康檢查：<http://127.0.0.1:5001/api/health>

更多細節請看 [README.backend.md](README.backend.md) 與 [README.frontend.md](README.frontend.md)。

---

## 📝 授權與免責聲明

此系統僅供教育與參考用途。使用者在購買、服用或停用任何藥物前，**務必諮詢醫生或藥師**。開發者不對因使用此系統而引起的任何後果負責。

**版本：** v2.x  
**更新日期：** 2026 年 6 月 18 日
