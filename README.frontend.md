# 📗 藥知道 — 前端 / iOS App 文件

Web 前端（年長者友好設計）與 Capacitor iOS App 封裝說明。

> 後端／API 請見 [README.backend.md](README.backend.md)。

---

## 🗂️ 前端結構

```
MUS_Project_v2/
├── index.html              # 使用者前端首頁（年長者友好）
├── admin.html              # 管理員後台 SPA
├── www/                    # Capacitor 同步後的前端輸出
│   └── index.html
├── ios/                    # Capacitor iOS 原生專案
│   ├── App/
│   │   ├── App/
│   │   │   ├── AppDelegate.swift
│   │   │   ├── Info.plist
│   │   │   └── Assets.xcassets/
│   │   └── App.xcodeproj/
│   └── CapApp-SPM/         # Swift Package
├── ios-native/             # 原生 iOS 實驗專案（保留）
├── package.json            # Capacitor 依賴
└── capacitor.config.json   # Capacitor 設定
```

---

## 🎨 Web 前端設計

### 設計理念（Apple HIG 風格 + 年長者優化）

| 項目 | 做法 |
|------|------|
| 字體 | 預設 18px，提供「正常 / 中 / 大」三段切換 |
| 色彩 | 日間：柔和綠植色；夜間：深紫藍漸變 + 毛玻璃 |
| 按鈕 | 每頁最多 3 個主要按鈕，大尺寸 + emoji 圖示 |
| 對比 | 文字對比度 > 4.5:1（WCAG AA） |
| 動畫 | 柔和過渡（200-300ms ease），無突兀彈跳 |
| 導航 | 清晰返回鈕，避免使用者迷路 |

### 使用者流程

```
[首頁]
  ├─ [拍照辨識]    → 選擇/拍照 → 上傳 → [辨識結果] → [藥物詳情]
  ├─ [藥單辨識]    → 拍攝藥單  → 上傳 → [批次辨識結果]
  ├─ [搜尋藥物]    → 輸入名稱  → [搜尋結果] → [藥物詳情]
  ├─ [我的用藥]    → 用藥清單 / 服藥紀錄 / 提醒設定
  └─ [AI 諮詢]     → 輸入問題  → 串流回應
```

### 兩支 HTML 入口

| 檔案 | 對象 | 路由 |
|------|------|------|
| `index.html` | 一般使用者 | `/` |
| `admin.html` | 管理員 | `/admin` |

兩支都是單一 HTML + 內嵌 JS（無 build step），透過 `fetch` 直接打後端 API。

---

## 🛠 管理員後台（admin.html）

進入 `http://127.0.0.1:5001/admin` 可用功能：

| # | 功能 | 說明 |
|---|------|------|
| 1 | 儀表板 | 藥物 / 圖片 / 快取 / 上傳統計 |
| 2 | 藥物管理 | CRUD、圖片上傳 |
| 3 | 使用者 | 帳號 / Profile 管理 |
| 4 | NHI 快取 | 健保署藥品資料快取維護 |
| 5 | 上傳檔案 | 暫存清理 |
| 6 | 設定 | 系統設定、舊版日誌檢視 |
| 7 | API 統計 | 端點呼叫量、Top 搜尋字 |
| 8 | AI 使用 | 依 provider / model 分項統計 |
| 9 | 📋 Log 紀錄 | 統一查詢 5 大類 log（系統 / API / AI / 服藥 / 安全） |
| 10 | 批次更新 | 從健保署 / TFDA 批次爬取藥物資料 |

### 「📋 Log 紀錄」頁特性

- Tab 切換 5 大類別（每類顯示總筆數）
- 共用篩選：關鍵字、開始 / 結束時間
- 類別專屬篩選：
  - 系統：等級（INFO / WARNING / ERROR / DEBUG）
  - API：Method、狀態碼
  - AI：功能、成功 / 失敗
  - 服藥 / 安全：User ID
- 分頁 50 筆，欄位依類別動態切換

---

## 📱 iOS App（Capacitor）

### 技術棧

| 元件 | 技術 |
|------|------|
| App 容器 | Capacitor 8.x |
| 前端 | `index.html`（與 Web 版相同） |
| 相機 | `@capacitor/camera` |
| 觸覺回饋 | `@capacitor/haptics` |
| 狀態列 | `@capacitor/status-bar` |
| 啟動畫面 | `@capacitor/splash-screen` |

### 前置要求

- macOS + Xcode 15+
- Node.js 18+
- CocoaPods 或 Swift Package Manager

### 建置步驟

```bash
# 安裝 Capacitor 依賴
npm install

# 同步 Web 前端到 www/ 並推進 iOS 專案
npx cap sync ios

# 開啟 Xcode
npx cap open ios
```

在 Xcode 中按 ▶ 即可在模擬器或實機執行。

### iOS 權限（已於 `ios/App/App/Info.plist` 設定）

| Key | 用途 |
|-----|------|
| `NSCameraUsageDescription` | 拍攝藥物照片 |
| `NSPhotoLibraryUsageDescription` | 從相簿選取藥物照片 |
| `NSPhotoLibraryAddUsageDescription` | 儲存辨識結果圖片 |
| `NSAppTransportSecurity` | 允許連線本地開發伺服器 |

### 連線後端

App 預設透過 `capacitor.config.json` 中的 `server.url` 或內嵌的 `fetch` 連到後端：

- 模擬器 → `http://127.0.0.1:5001`
- 實機 → `http://<電腦區網 IP>:5001`（例：`http://192.168.1.103:5001`）

修改 `index.html` 內的 `API_BASE` 常數即可切換。

---

## 🧪 測試前端

### Web 瀏覽器

1. 啟動後端：`$env:PORT="5001"; python main.py`
2. 開 <http://127.0.0.1:5001/>
3. 點「拍照辨識藥物」上傳測試圖片

### cURL

```bash
# 健康檢查
curl http://127.0.0.1:5001/api/health

# 搜尋藥物
curl -X POST http://127.0.0.1:5001/api/search \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"普拿疼\",\"limit\":5}"
```

### iOS 實機

1. 確認 Mac 與 iPhone 在同一區網
2. 修改 `index.html` 的 `API_BASE` 為電腦 IP
3. 在 Xcode 選擇實機 → ▶
4. 首次執行需在 iPhone「設定 → 一般 → VPN 與裝置管理」信任開發者憑證

---

## 🐛 前端常見問題

### Q: iOS App 顯示「無法連線」
**A:**
1. 後端是否啟動？`curl http://127.0.0.1:5001/api/health` 回 200 才算正常
2. 實機需用區網 IP（不是 `127.0.0.1`）
3. `Info.plist` 的 `NSAppTransportSecurity → NSAllowsArbitraryLoads` 應為 `true`（開發階段）

### Q: `npx cap sync ios` 報錯
**A:**
1. 先 `npm install` 確保所有 Capacitor 套件版本一致
2. 在 `ios/App/` 跑 `pod install --repo-update`

### Q: 上傳圖片後顯示「未能識別」
**A:**
1. 光線充足、藥物清晰置中
2. 嘗試不同角度
3. 確認圖片格式為 JPG / PNG，大小 < 10MB

### Q: 後台「Log 紀錄」頁打不開
**A:** 後端需是 `feature/prescription-admin-fixes` 之後的版本（含 `services/system_log.py` 與 `/admin/api/logs/*` 端點）。

---

## 🎨 樣式調整建議

- 改變主色：搜尋 `index.html` 中的 `--primary-color` CSS 變數
- 改變字體大小預設：搜尋 `localStorage.getItem('fontSize')`
- 切換日／夜模式預設：搜尋 `localStorage.getItem('theme')`

兩支 HTML 都是純 vanilla JS，沒有 build 流程；改完直接重新整理瀏覽器即可。
