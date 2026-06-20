# 📱 藥知道 — iOS App 文件

原生 SwiftUI iOS App，提供完整的智慧用藥管理體驗。

> 後端／API 請見 [README.backend.md](README.backend.md)。  
> Web 前端請見 [README.frontend.md](README.frontend.md)。

---

## 🗂️ 專案結構

```
ios-native/
├── MUS-iOS.xcodeproj/              # Xcode 專案
├── MUS-iOS/
│   ├── App/                        # App 入口
│   │   ├── MUS_iOSApp.swift        # @main App
│   │   └── AppEnvironment.swift    # 全域環境（API client、設定）
│   │
│   ├── Core/                       # 核心模組
│   │   ├── Network/
│   │   │   ├── APIClient.swift     # API 協定定義
│   │   │   └── RealAPIClient.swift # 實際 API 實作（JWT 認證）
│   │   ├── Storage/
│   │   │   └── Models.swift        # 資料模型（Drug, Medication, MedicationRecord 等）
│   │   └── Notifications/
│   │       └── NotificationManager.swift
│   │
│   ├── DesignSystem/               # 統一設計系統
│   │   ├── DesignColors.swift      # 色彩定義
│   │   ├── DesignTypography.swift  # 字型定義
│   │   └── Components/            # 可重用 UI 元件（Card, SpacedButton 等）
│   │
│   ├── Features/                   # 功能模組
│   │   ├── Auth/                   # 登入 / 註冊
│   │   ├── Home/                   # 首頁
│   │   ├── Recognition/           # 藥物拍照辨識
│   │   ├── Medications/           # 用藥管理（核心功能）
│   │   │   ├── MedicationsListView.swift    # 藥物列表
│   │   │   ├── MedicationDetailView.swift   # 藥物詳情
│   │   │   ├── MedicationConfirmView.swift  # 確認服藥
│   │   │   ├── MedicationStore.swift        # 資料管理（ObservableObject）
│   │   │   ├── AddMedicationView.swift      # 新增藥物
│   │   │   ├── PrescriptionDraftView.swift  # 藥單 OCR → 批次新增
│   │   │   └── AdherenceStatsView.swift     # 服藥統計
│   │   ├── Safety/                # 安全檢查（過敏 / 交互作用）
│   │   ├── Consultation/         # AI 藥師諮詢
│   │   ├── Pharmacy/             # 附近藥局
│   │   └── Profile/              # 個人設定 / 多 Profile
│   │
│   ├── Mocks/                     # Mock 資料（預覽 / 測試用）
│   │   ├── MockAPIClient.swift
│   │   └── MockData.swift
│   │
│   └── Resources/
│       └── Localizable.xcstrings  # 多語系字串
│
└── Tests/                         # 單元測試
```

---

## ⚙️ 技術棧

| 項目 | 技術 |
|------|------|
| 語言 | Swift 5.9+ |
| UI 框架 | SwiftUI |
| 最低版本 | iOS 16.0 |
| Bundle ID | `com.mus2.drugrecognition` |
| 架構 | MVVM（View + ObservableObject Store） |
| 網路層 | URLSession + async/await |
| 認證 | JWT（Bearer Token） |
| 資料格式 | JSON（snake_case ↔ camelCase 自動轉換） |
| 本地快取 | UserDefaults + Codable（LocalCache） |

---

## 🚀 建置與執行

### 前置要求

- macOS 14+ (Sonoma)
- Xcode 15+
- iOS 16.0+ 模擬器或實機

### 命令列建置

```bash
cd ios-native

# 建置
xcodebuild -project MUS-iOS.xcodeproj \
  -scheme MUS-iOS \
  -destination 'platform=iOS Simulator,name=iPhone 16' \
  build

# 安裝到模擬器
xcrun simctl install "iPhone 16" \
  ~/Library/Developer/Xcode/DerivedData/MUS-iOS-*/Build/Products/Debug-iphonesimulator/藥知道.app

# 啟動
xcrun simctl launch "iPhone 16" com.mus2.drugrecognition
```

### Xcode 建置

1. 打開 `ios-native/MUS-iOS.xcodeproj`
2. 選擇 scheme「MUS-iOS」
3. 選擇目標裝置（模擬器或實機）
4. 按 ▶ 執行

---

## 🔌 連線後端

App 透過 `RealAPIClient` 連線 Flask 後端：

| 環境 | 後端位址 |
|------|---------|
| 遠端伺服器 | `http://100.82.235.49:5001`（Tailscale） |
| 本地開發 | `http://127.0.0.1:5001` |
| 實機測試 | `http://<電腦區網 IP>:5001` |

修改 `AppEnvironment.swift` 中的 `baseURL` 即可切換。

---

## 📋 主要功能

### 藥物辨識
- 📷 拍照辨識單顆藥物
- 📋 整張藥單 OCR 辨識（支援處方箋）
- 批次匯入辨識結果到用藥清單

### 用藥管理
- 💊 藥物清單（依藥單 / 時段分類）
- ✅ 確認服藥 + 超量警告
- ↩️ 撤銷誤按的服藥紀錄（5 秒 undo bar + 詳情頁撤銷按鈕）
- 📊 庫存追蹤（剩餘天數 / 低庫存提醒）
- 📈 服藥統計與遵從率

### 安全檢查
- ⚠️ 過敏提醒
- 💊 藥物交互作用檢查
- 🔄 重複用藥偵測

### 其他
- 🤖 AI 藥師諮詢（串流回應）
- 🏥 附近藥局查詢（地圖）
- 👨‍👩‍👧 多 Profile（管理家人用藥）
- 🔔 服藥提醒推播

---

## 🐛 常見問題

### Q: App 顯示「無法連線」
**A:**
1. 確認後端已啟動：`curl http://100.82.235.49:5001/api/health`
2. 確認 Tailscale 已連線（或改用區網 IP）
3. 確認 `AppEnvironment` 中的 `baseURL` 正確

### Q: 模擬器啟動 App 失敗（No such process）
**A:**
1. 模擬器可能未完全啟動，等幾秒後再試
2. 重新安裝 App：先 build 再 `xcrun simctl install`

### Q: 確認服藥後庫存沒變
**A:** 庫存由後端計算，確認後端 `routes/medications.py` 的 `log_adherence` 有正確扣減 `stock_qty`。

---

## 📱 舊版 Capacitor App（已棄用）

舊版使用 Capacitor 8 封裝 Web 前端，位於 `ios/` 目錄。現已改用原生 SwiftUI 開發，舊版僅作為歷史參考保留。

```
ios/                    # Capacitor 舊版（不再維護）
├── App/
│   ├── App/
│   │   ├── AppDelegate.swift
│   │   └── Info.plist
│   └── App.xcodeproj/
├── CapApp-SPM/
└── capacitor-cordova-ios-plugins/
```
