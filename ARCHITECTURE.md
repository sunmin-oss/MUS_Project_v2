# 系統架構與設計文件 - MUS2

## 📐 系統架構圖

```
┌─────────────────────────────────────────────────────┐
│              用戶介面層 (Frontend)                  │
│  ┌──────────────────────────────────────────────┐  │
│  │          index.html (年長者友好設計)          │  │
│  │  • 大字體 (18px+)                            │  │
│  │  • 高對比度                                  │  │
│  │  • 簡單導航 (< 3 個按鈕)                    │  │
│  │  • 響應式設計                                │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────┬───────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼───────────────────────────┐
│              API 層 (Flask Backend)                 │
│  ┌──────────────────────────────────────────────┐  │
│  │              main.py                          │  │
│  │  ✓ POST /api/recognize                       │  │
│  │  ✓ POST /api/search                          │  │
│  │  ✓ GET  /api/health                          │  │
│  │  ✓ GET  /api/drug/<id>                       │  │
│  │  ✓ 錯誤處理 & 日誌                            │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────┬──────────────────────┐   │
│  │   Vision API 層     │   資料庫層            │   │
│  ├─────────────────────┼──────────────────────┤   │
│  │ • Google Vision     │ • drug_database.py   │   │
│  │ • Claude Vision     │   - search_by_name   │   │
│  │                     │   - get_by_id        │   │
│  └─────────────────────┴──────────────────────┘   │
└────────────────────────┬───────────────────────────┘
              ┌──────────┴──────────┐
              ▼                      ▼
      ┌─────────────────┐   ┌──────────────────┐
      │  Google Cloud  │   │  SQLite Database │
      │  Vision API    │   │ (drug_recognition│
      │                │   │      .db)        │
      └─────────────────┘   └──────────────────┘
```

## 🔄 用戶交互流程

```
用戶               前端              後端              API
 │                 │                 │                 │
 ├─ 打開應用 ──→  首頁顯示          │                 │
 │                 │                 │                 │
 ├─ 選擇「拍照」──→ 上傳界面         │                 │
 │                 │                 │                 │
 ├─ 上傳圖片 ──→ 驗證 & 儲存 ──→ main.py            │
 │                 │             ├─────────────→ Google Vision
 │                 │             │               或 Claude API
 │                 │             └──→ 獲取辨識結果   │
 │                 │             ├─ 搜索資料庫      │
 │                 │             └─ 組合結果        ▼
 │                 │←─ 回傳結果 ──────┤
 │                 │                  │
 ├─ 查看結果 ──→ 顯示匹配藥物        │
 │                 │                  │
 ├─ 點擊詳情 ──→ 發送 GET 請求 ──→ 查詢資料庫
 │                 │←─ 回傳詳情 ──────┤
 └─ 查看完整資訊 ← 顯示藥物詳細      │
```

## 🗂️ 檔案責任分區

| 檔案 | 負責功能 | 依賴 |
|-----|---------|------|
| `main.py` | Flask 應用、路由、錯誤處理 | Flask, CORS |
| `config.py` | 配置管理、環境變數 | dotenv, pathlib |
| `vision_api_google.py` | Google Vision API 包裝 | requests, base64 |
| `vision_api_claude.py` | Claude Vision API 包裝 | requests, base64, json |
| `drug_database.py` | 藥物資料庫查詢 | sqlite3 |
| `index.html` | 使用者介面、客戶端邏輯 | Vue.js（可選，現在用原生 JS） |
| `.env` | 敏感配置（API 密鑰） | - |
| `requirements.txt` | Python 依賴列表 | - |

## 🔌 API 設計原則

### 1. 簡潔性
- 最少化的參數
- 直觀的端點命名
- 統一的回應格式

### 2. 魯棒性
```python
{
    "success": bool,      # 成功標誌
    "data": {...},        # 響應資料
    "error": "msg",       # 錯誤訊息（失敗時）
    "message": "info"     # 補充訊息
}
```

### 3. 可擴展性
- 預留 `metadata` 欄位
- 支援分頁（`limit`, `offset`）
- 版本控制（未來可演變為 `/api/v2/`）

## 🎨 前端設計原則

### 色彩方案
- **主色：** 紫色 (#667eea) - 給人信任感
- **輔色：** 深紫色 (#764ba2) - 深度感
- **背景：** 白色 - 清晰
- **文字：** 深灰色 (#333) - 高對比度

### 字體選擇
- **主字體：** 微軟正黑體（Windows）
- **備用字體：** Arial（通用）
- **大小：** 18px+（易讀）

### 交互設計
- **按鈕最小尺寸：** 80px × 25px（便於觸摸）
- **響應時間：** < 200ms（視覺反饋迅速）
- **頁面轉換：** 0.3s 淡入效果

## 📡 API 呼叫流程

### 圖片辨識流程

```
使用者上傳圖片
    ↓
[前端] 驗證檔案類型和大小
    ↓
[前端] 將檔案編碼為 FormData
    ↓
POST /api/recognize
    ↓
[後端] 驗證請求
    ├─ 檢查 Content-Type
    ├─ 檢查檔案大小
    ├─ 驗證檔案擴展名
    └─ 檢查 API 可用性
    ↓
儲存上傳的臨時檔案
    ↓
呼叫 Vision API
    ├─ [Google] 標籤檢測 + OCR + 物體偵測
    └─ [Claude] 自然語言分析
    ↓
解析 API 回應，提取藥物名稱
    ↓
查詢本地資料庫
    ├─ 按名稱搜尋
    ├─ 提取詳細資訊（許可證、成分等）
    └─ 組合最終結果
    ↓
返回 JSON 回應
    ↓
[前端] 渲染結果，顯示給使用者
```

## 🔐 安全性考量

### 1. 檔案上傳安全
```python
# ✓ 白名單擴展名驗證
# ✓ 檔案大小限制 (10MB)
# ✓ 檔名淨化（防止路徑遍歷）
# ✓ 儲存在受保護的目錄
```

### 2. API 密鑰保護
```bash
# ✓ 絕不硬編碼
# ✓ 通過環境變數傳遞
# ✓ .env 檔案不上傳到 Git
# ✓ 生成環境中使用祕密管理
```

### 3. 輸入驗證
```python
# ✓ 搜尋字串長度限制
# ✓ SQL 注入防護（使用參數化查詢）
# ✓ XSS 防護（返回 JSON，不直接渲染 HTML）
```

## ⚡ 性能優化策略

### 後端最佳化
1. **API 快取**
   ```python
   from flask_caching import Cache
   cache = Cache(app, config={'CACHE_TYPE': 'redis'})
   ```

2. **資料庫索引**
   ```sql
   CREATE INDEX idx_drug_name ON drugs(chinese_name, english_name);
   CREATE INDEX idx_license ON drugs(license_number);
   ```

3. **非同步處理**
   ```python
   from celery import Celery
   # 處理長時間執行的任務
   ```

### 前端最佳化
1. **圖片壓縮**
   ```javascript
   // 上傳前壓縮圖片
   ```

2. **懶加載**
   ```javascript
   // 只載入可見元素
   ```

3. **快取策略**
   ```javascript
   // LocalStorage 儲存最近查詢
   ```

## 🌐 跨平台相容性

### 瀏覽器支持
- ✓ Chrome/Chromium (90+)
- ✓ Firefox (88+)
- ✓ Safari (14+)
- ✓ Edge (90+)
- ✓ 微信內置瀏覽器

### 行動裝置
- ✓ iOS 12+
- ✓ Android 8+
- ✓ 響應式設計 (480px-2560px)

### 無障礙設計
- ✓ ARIA 標籤（視覺障礙人士）
- ✓ 鍵盤導航支持
- ✓ 高對比度色彩
- ✓ 大字體選項

## 📊 數據流向

```
輸入層                    處理層                輸出層
┌───────────┐      ┌──────────────┐      ┌─────────┐
│ 圖片上傳  │      │ Vision API   │      │ JSON    │
├───────────┤  ──→ ├──────────────┤  ──→ ├─────────┤
│ 文字搜尋  │      │ 資料庫查詢   │      │ HTML    │
└───────────┘      └──────────────┘      └─────────┘
     │                    │                    │
     └── 驗證 ─→ 存儲 ─────┴── 整合 ─→ 格式化 ─┘
```

## 🚀 部署拓撲

### 開發環境
```
開發機 → Flask 開發伺服器 (localhost:5000)
            ↓
        SQLite DB + Google API
```

### 生產環境
```
使用者 → Nginx (反向代理) → Gunicorn (4-8 workers)
             ↓
         Flask 應用
             ↓
         SQLite/PostgreSQL
             ↓
         Google Cloud Vision API
```

### Docker 部署
```
使用者 → Docker Compose
         ├─ mus2-app 容器 (Python 3.10)
         ├─ volumes (uploads, db)
         └─ 網路暴露 :5000
```

## 📈 可擴展性路線圖

### Phase 1 (現在)
- [x] 基本 Vision API 整合
- [x] 簡化 UI
- [x] 資料庫查詢

### Phase 2 (未來)
- [ ] 多語言支持
- [ ] 離線模式（PWA）
- [ ] 使用者帳戶
- [ ] 查詢歷史

### Phase 3 (長期)
- [ ] 機器學習優化
- [ ] 社群反饋系統
- [ ] 藥物相互作用檢查
- [ ] 移動應用原生版

## 📝 編碼標準

### Python 風格
- PEP 8 標準
- 類型提示
- 完整的文件字符串

```python
def recognize_drug(image_path: str) -> List[Dict[str, Any]]:
    """
    識別圖片中的藥物
    
    Args:
        image_path: 圖片檔案路徑
    
    Returns:
        藥物識別結果列表
    
    Raises:
        FileNotFoundError: 檔案不存在
        ValueError: 無效的檔案格式
    """
```

### JavaScript 風格
- 駝峰命名
- const/let（禁用 var）
- 箭頭函數

```javascript
const recognizeDrug = async (file) => {
    // 實作
};
```

## 🔍 測試策略

### 後端測試
```python
# tests/test_api.py
def test_recognize_endpoint():
    response = client.post('/api/recognize', 
                          data={'image': test_image})
    assert response.status_code == 200
    assert 'recognized_items' in response.json
```

### 前端測試
```javascript
// tests/ui.test.js
describe('Drug Recognition UI', () => {
    test('Should display results after upload', () => {
        // 測試邏輯
    });
});
```

---

**文件版本：** 1.0  
**最後更新：** 2025 年 2 月 27 日  
**維護者：** MUS2 開發團隊
