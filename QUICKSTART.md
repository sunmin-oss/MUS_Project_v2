# 快速部署指南 - MUS2 簡化版藥物辨識系統

## 🚀 30 分鐘快速啟動

### 第一步：準備 API 密鑰 (5 分鐘)

#### 選項 A：使用 Google Vision API （推薦）

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 點擊「建立專案」
3. 專案名稱：例如「MUS2 藥物辨識」
4. 在頂部搜尋框搜尋「Vision API」
5. 點擊「Vision API」→ 「啟用」
6. 左側選單 → 「認證」→ 「建立認證」→ 「服務帳號」
7. 填入帳號詳細資訊，點擊「建立及繼續」
8. 在「金鑰」標籤下，點擊「新增金鑰」→「建立新的金鑰」→「JSON」
9. 複製整個 JSON 內容到記事本，稍後使用

#### 選項 B：使用 Claude Vision API

1. 前往 [Anthropic 官方網站](https://www.anthropic.com/)
2. 進入「Console」或開發者頁面
3. 複製您的 API 密鑰

### 第二步：設置環境 (5 分鐘)

#### Windows 用戶

```batch
REM 1. 打開命令提示字元，進入 MUS2 資料夾
cd d:\大學\專題\MUS2

REM 2. 建立虛擬環境
python -m venv venv

REM 3. 激活虛擬環境
venv\Scripts\activate

REM 4. 安裝依賴
pip install -r requirements.txt
```

#### macOS/Linux 用戶

```bash
# 1. 進入 MUS2 資料夾
cd ~/path/to/MUS2

# 2. 建立虛擬環境
python3 -m venv venv

# 3. 激活虛擬環境
source venv/bin/activate

# 4. 安裝依賴
pip install -r requirements.txt
```

### 第三步：配置密鑰 (5 分鐘)

1. 在 MUS2 資料夾中複製 `.env.example` 為 `.env`
2. 編輯 `.env` 檔案，填入您的 API 密鑰：

```
# Google Vision (推薦)
API_PROVIDER=google
GOOGLE_VISION_API_KEY=your_key_here

# 或 Claude
# API_PROVIDER=claude
# CLAUDE_API_KEY=your_key_here
```

### 第四步：添加藥物資料庫（可選但推薦）(5 分鐘)

```bash
# 從 MUS_Project 複製資料庫到 MUS2 資料夾
cp ../MUS_Project/drug_recognition.db ./
```

### 第五步：啟動系統 (5 分鐘)

#### 開發模式

```bash
# 確保虛擬環境激活
python main.py
```

然後打開瀏覽器訪問：**http://localhost:5000**

#### 生產模式 (部署到伺服器)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

---

## 🐳 使用 Docker 快速部署 (推薦用於伺服器)

### 要求
- 安裝 [Docker](https://www.docker.com/)
- 安裝 [Docker Compose](https://docs.docker.com/compose/install/)

### 步驟

```bash
# 1. 進入 MUS2 資料夾
cd MUS2

# 2. 複製環境檔案
cp .env.example .env

# 3. 編輯 .env 填入 API 密鑰
# 使用您喜歡的編輯器編輯 .env

# 4. 啟動容器
docker-compose up -d

# 系統將在 http://localhost:5000 運行
```

### 查看日誌
```bash
docker-compose logs -f mus2-app
```

### 停止服務
```bash
docker-compose down
```

---

## ☁️ 部署到雲平台

### Vercel (前端靜態檔案)

1. 建立 `vercel.json`：
```json
{
  "builds": [
    { "src": "index.html", "use": "@vercel/static" }
  ]
}
```

2. 部署到 Vercel
3. 配置環境變數指向後端 API (例如 Render 或 Heroku)

### Render (後端)

1. 在 Render 上建立新的「Web Service」
2. 連接 GitHub 倉庫（或推送程式碼）
3. 設置環境變數：
   - `GOOGLE_VISION_API_KEY`
   - `API_PROVIDER=google`
   - `FLASK_ENV=production`

4. 部署設定：
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn -w 4 -b 0.0.0.0:5000 main:app`

### Heroku (後端)

```bash
# 1. 安裝 Heroku CLI
# 2. 登入
heroku login

# 3. 建立應用
heroku create mus2-app

# 4. 設置環境變數
heroku config:set GOOGLE_VISION_API_KEY=your_key
heroku config:set API_PROVIDER=google

# 5. 部署
git push heroku main
```

---

## 🧪 測試系統是否正常運行

### 使用瀏覽器
1. 打開 http://localhost:5000
2. 點擊「拍照辨識藥物」
3. 上傳或拍攝藥物圖片
4. 查看識別結果

### 使用命令列測試

```bash
# 測試 API 健康狀態
curl http://localhost:5000/api/health

# 搜尋藥物（需要資料庫）
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"普拿疼"}'
```

**預期回應：** 應該看到 JSON 格式的結果

---

## 🔧 故障排除

### 問題：「ModuleNotFoundError: No module named 'flask'」

**解決方案：**
```bash
# 確認虛擬環境已激活
# Windows: 應該顯示 (venv) 前綴
# 重新安裝依賴
pip install -r requirements.txt
```

### 問題：「google.auth.exceptions.DefaultCredentialsError」

**解決方案：**
1. 檢查 `.env` 檔案中的 `GOOGLE_VISION_API_KEY`
2. 確認密鑰已正確複製（沒有額外空格）
3. 確認 API_PROVIDER 設置為 'google'

### 問題：「辨識後顯示未能識別」

**解決方案：**
1. 確保光線充足
2. 拍攝清晰的藥物照片（建議白色背景）
3. 確認圖片格式支持（JPG, PNG）
4. 查看服務器日誌了解詳細錯誤

### 問題：「資料庫不存在」

**解決方案：**
系統可以在沒有資料庫的情況下運行（僅辨識，無詳細查詢），或：
1. 複製 `drug_recognition.db` 到 MUS2 資料夾
2. 或建立空資料庫（系統會自動適應結構）

---

## 📊 性能建議

### 對於小型部署（< 100 日活用戶）
- 本地 Flask 開發伺服器足夠
- 無需 Redis 或資料庫快取

### 對於中型部署（100-1000 日活用戶）
```bash
# 使用 Gunicorn + Nginx 反向代理
gunicorn -w 4 -b unix:app.sock main:app
```

### 對於大型部署（> 1000 日活用戶）
- 使用 Kubernetes 進行容器編排
- 添加 Redis 快取層
- 使用 CDN 加速靜態資源
- 設置負載均衡器

---

## 🔐 安全考量

### 生產環境部署前

1. **更改預設設置**
   - 修改 `config.py` 中的密鑰設置
   - 禁用除錯模式

2. **設置 HTTPS**
   ```nginx
   # nginx 配置
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

3. **限制 API 速率**
   ```python
   from flask_limiter import Limiter
   limiter = Limiter(app)
   
   @app.route('/api/recognize')
   @limiter.limit("10 per minute")
   def recognize_drug():
       ...
   ```

4. **添加驗證**
   ```python
   from functools import wraps
   
   def require_api_key(f):
       @wraps(f)
       def decorated(*args, **kwargs):
           key = request.headers.get('X-API-Key')
           if key != os.getenv('API_KEY'):
               return jsonify({'error': 'Unauthorized'}), 401
           return f(*args, **kwargs)
       return decorated
   ```

---

## 📈 監控和日誌

### 啟用詳細日誌

```bash
# 編輯 .env
LOG_LEVEL=DEBUG
```

### 使用 Supervisor 保持應用運行（Linux）

```bash
# /etc/supervisor/conf.d/mus2.conf
[program:mus2]
directory=/path/to/MUS2
command=/path/to/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 main:app
autostart=true
autorestart=true
stderr_logfile=/var/log/mus2.err.log
stdout_logfile=/var/log/mus2.out.log
```

---

## 📞 獲取幫助

如遇到問題：
1. 查看 README.md 常見問題部分
2. 檢查服務器日誌（使用 `docker-compose logs`）
3. 確認 API 密鑰是否正確
4. 測試 `/api/health` 端點

---

**快速連結：**
- [系統 README](README.md)
- [API 文件](README.md#-api-文件)
- [GitHub Issues](https://github.com)

**更新日期：** 2025 年 2 月 27 日
