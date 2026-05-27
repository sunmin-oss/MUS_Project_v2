# iOS App 開發規劃單（SwiftUI Native）

> 文件版本：v1.0 Draft
> 對應 Feature Specs：01–06（docs/features/）
> 對應 Backend Roadmap：docs/BACKEND_ROADMAP.md
> 平台：iOS 16.0+，SwiftUI（原生）
> 策略：**UI Mock 先行**，後端就緒後接 API

---

## 1. 技術棧

| 項目 | 選型 | 理由 |
|---|---|---|
| 語言 | Swift 5.9+ | 競賽鼓勵 + 長期維護 |
| UI Framework | SwiftUI（主）+ UIKit（必要時橋接） | 宣告式 UI、現代化 |
| 最低支援 | iOS 16.0 | 涵蓋 95%+ 裝置 |
| 架構模式 | MVVM + Repository | 易測試、清楚分層 |
| 非同步 | async/await + Combine | 原生整合 |
| 網路層 | URLSession + Codable | 不引入第三方 |
| 本地儲存 | **Core Data**（iOS 16 相容） | 用藥資料本地快取 |
| 影像處理 | AVFoundation + Vision | 相機 / OCR 預處理 |
| 推播 | UserNotifications + APNs | 用藥提醒 |
| 圖表 | Swift Charts | 服藥順從率視覺化 |
| 地圖 | MapKit | 藥局地圖 |
| Keychain | KeychainAccess（or 自寫 wrapper） | JWT/Refresh Token 安全儲存 |
| 訂閱 | StoreKit 2 | 訂閱方案 |

**不引入大型第三方依賴**（Alamofire、RxSwift 等），保持 App 輕量與審核友善。

---

## 2. 專案結構

```
MUS-iOS/
├─ App/
│  ├─ MUSApp.swift              # App entry
│  └─ AppCoordinator.swift      # 全域路由
├─ Core/
│  ├─ Network/                  # URLSession wrapper, APIClient
│  ├─ Auth/                     # JWT 管理、Keychain
│  ├─ Storage/                  # SwiftData models
│  ├─ Notifications/            # 推播註冊與排程
│  └─ Utils/                    # 共用工具
├─ Features/
│  ├─ Auth/                     # 登入、註冊、OAuth
│  ├─ Recognition/              # 藥品辨識（現有核心）
│  ├─ Medications/              # Spec 01 個人用藥
│  ├─ Consultation/             # Spec 02 藥師諮詢
│  ├─ Pharmacy/                 # Spec 03 藥局地圖
│  ├─ Knowledge/                # Spec 04 知識卡片
│  ├─ Subscription/             # Spec 05 訂閱
│  ├─ Safety/                   # Spec 06 安全警示
│  └─ Profile/                  # 個人/家庭成員管理
├─ DesignSystem/
│  ├─ Colors.swift              # 色票
│  ├─ Typography.swift          # 字型（長者友善大字）
│  ├─ Components/               # 可重用元件
│  └─ Modifiers/                # ViewModifier
├─ Resources/
│  ├─ Assets.xcassets
│  ├─ Localizable.xcstrings     # 中文/英文
│  └─ Info.plist
└─ Mocks/
   └─ MockData/                 # UI Mock 階段假資料
```

---

## 3. 設計系統（Design System）

針對「年長者友善」的核心使用者，必須優先考量：

| 項目 | 設計準則 |
|---|---|
| 字級 | 最小 17pt（內文），標題 ≥ 22pt；支援 Dynamic Type |
| 對比 | 文字對比度 ≥ 7:1（WCAG AAA）|
| 觸控目標 | 最小 44×44pt |
| 配色 | 主色高飽和度；避免淺灰文字 |
| 動畫 | 提供「減少動畫」開關 |
| 語音 | 重要功能支援 VoiceOver |
| 暗色模式 | 完整支援 |
| 觸覺 | 重要操作 + 警示用 Haptics 強化 |

---

## 4. 階段規劃（Phase-by-Phase）

### Phase 0：專案骨架與設計系統（前置）

**目標**：建立可運作的空 App + 設計系統 + Mock 資料層

- [ ] P0.1 在 `ios-native/` 建立新 Xcode SwiftUI 專案
- [ ] P0.2 Bundle ID 沿用 `com.mus2.drugrecognition`，名稱「藥知道」
- [ ] P0.3 設計系統：色票、字型、共用元件（Button、Card、Alert）
- [ ] P0.4 建立 Mock 資料層：`MockDataProvider`（產生假藥品、假提醒、假諮詢）
- [ ] P0.5 建立 `APIClient` 骨架（Protocol-based，方便切換 Mock/Real）
- [ ] P0.6 建立 Tab Bar 導覽骨架（首頁/用藥/諮詢/我的）
- [ ] P0.7 整合 Localizable.xcstrings（繁中為主）

### Phase 1：MVP 核心功能（UI Mock）

**對應 Spec 06 + 01 + 03 的 UI 部分**

#### 1A. 藥品辨識（現有功能原生化）
- [ ] P1A.1 相機/相簿拍照（AVFoundation + PHPickerViewController）
- [ ] P1A.2 影像預處理：自動裁切、亮度調整
- [ ] P1A.3 上傳 + 辨識結果頁面 UI
- [ ] P1A.4 辨識結果詳情頁（藥品資訊、副作用、注意事項）
- [ ] P1A.5 辨識歷史紀錄頁

#### 1B. 個人用藥管理（Spec 01）
- [ ] P1B.1 Profile 切換 UI（本人/家人）
- [ ] P1B.2 我的用藥清單頁
- [ ] P1B.3 新增/編輯藥品表單
- [ ] P1B.4 用藥提醒時間設定 UI
- [ ] P1B.5 服藥確認 Modal（從推播 deep link）
- [ ] P1B.6 服藥日曆視圖（Swift Charts）
- [ ] P1B.7 順從率統計頁
- [ ] P1B.8 處方箋拍照 → OCR 草稿確認頁

#### 1C. 藥局地圖（Spec 03）
- [ ] P1C.1 MapKit 整合
- [ ] P1C.2 「我附近」藥局列表 + 篩選（營業中/健保特約/24h）
- [ ] P1C.3 藥局詳情頁（電話、導航、加入最愛）
- [ ] P1C.4 最愛藥局頁

#### 1D. 安全警示（Spec 06）
- [ ] P1D.1 安全警示 Modal 元件（4 級顏色/行為）
- [ ] P1D.2 過敏清單管理頁
- [ ] P1D.3 個人健康屬性設定（懷孕/哺乳/慢性病等）
- [ ] P1D.4 用藥檢查觸發點整合（新增藥品時自動觸發）

#### 1E. 推播通知
- [ ] P1E.1 推播權限請求 UI
- [ ] P1E.2 本地通知排程（UNUserNotificationCenter）
- [ ] P1E.3 通知 Action（已服/延後/略過）
- [ ] P1E.4 補藥提醒（庫存倒數）

### Phase 2：擴展功能（UI Mock）

#### 2A. AI 藥師諮詢（Spec 02）
- [ ] P2A.1 聊天介面 UI（訊息泡泡、輸入框）
- [ ] P2A.2 圖片諮詢 UI
- [ ] P2A.3 諮詢歷史列表
- [ ] P2A.4 「轉真人藥師」CTA UI
- [ ] P2A.5 真人藥師預約流程 UI（藥師列表 → 時段選擇 → 確認）

#### 2B. 知識卡片（Spec 04）
- [ ] P2B.1 卡片瀏覽頁（按分類 / 推薦）
- [ ] P2B.2 卡片詳情頁
- [ ] P2B.3 收藏管理頁
- [ ] P2B.4 卡片分享（Share Sheet + OG Image）

#### 2C. 訂閱與額度（Spec 05）
- [ ] P2C.1 訂閱方案介紹頁（Free/Pro/Family）
- [ ] P2C.2 StoreKit 2 整合：購買流程
- [ ] P2C.3 訂閱狀態管理（Subscription View Model）
- [ ] P2C.4 各功能額度檢查 + 升級引導 UI

#### 2D. 用藥歷史 PDF 匯出
- [ ] P2D.1 匯出設定頁（範圍選擇）
- [ ] P2D.2 觸發後端產生 PDF（Phase 3 接 API）
- [ ] P2D.3 Quick Look 預覽 + 分享

### Phase 3：後端串接（取代 Mock）

**前置條件**：對應 Backend Roadmap Phase 0/1 完成

- [ ] P3.1 認證流程接 API（註冊/登入/OAuth/Refresh）
- [ ] P3.2 Keychain 儲存 Token，APIClient 自動帶 JWT
- [ ] P3.3 Token 過期自動 Refresh
- [ ] P3.4 替換 Phase 1 各模組的 MockDataProvider → 真實 API
- [ ] P3.5 推播 Token 註冊到後端
- [ ] P3.6 離線快取策略（SwiftData 寫入 + 重連同步）
- [ ] P3.7 錯誤處理統一（網路 / 401 / 403 / 5xx）

### Phase 4：拋光與上架

- [ ] P4.1 完整 VoiceOver 支援
- [ ] P4.2 Dynamic Type 全頁面測試
- [ ] P4.3 暗色模式全頁面測試
- [ ] P4.4 App Icon + Launch Screen 美化
- [ ] P4.5 App Store 截圖、描述、隱私權標示
- [ ] P4.6 TestFlight Beta 測試
- [ ] P4.7 App Store 送審

---

## 5. 與 Backend 的同步策略

| App Phase | Backend 依賴 | Mock 對應 |
|---|---|---|
| Phase 0 | 無 | — |
| Phase 1（UI Mock）| 無 | 全 Mock |
| Phase 2（UI Mock）| 無 | 全 Mock |
| Phase 3（接 API）| Backend Phase 0+1 完成 | 逐步取代 |
| Phase 4 | Backend Phase 2 完成 | — |

**APIClient 設計**：採 Protocol-based，可隨時切換 Mock / Real：

```swift
protocol APIClientProtocol {
    func recognizeDrug(image: Data) async throws -> RecognitionResult
    func fetchMedications(profileId: String) async throws -> [Medication]
    // ...
}

class MockAPIClient: APIClientProtocol { /* 假資料 */ }
class RealAPIClient: APIClientProtocol { /* URLSession */ }
```

---

## 6. 風險與依賴

| 風險 | 影響 | 對策 |
|---|---|---|
| Spec 變更導致 UI 重做 | 中 | Mock 階段保持 ViewModel 與 View 解耦 |
| 推播需要 Apple Developer 帳號（付費）| 高 | 提早申請 |
| 訂閱需 App Store Connect 設定 | 中 | Phase 2 前完成 |
| Backend Phase 1 延遲 | 中 | App Phase 3 可延後，先深化 UI |
| 處方箋 OCR 精度 | 中 | UI 設計可編輯草稿，緩衝 OCR 誤差 |
| 競賽期限 | 高 | 優先 Phase 1 MVP，Phase 2 視時間決定 |

---

## 7. 已決議事項

- ✅ 採 SwiftUI 原生（重寫 UI）
- ✅ 只開發 iOS（Android、iPad/Mac Catalyst 不支援）
- ✅ 涵蓋 6 個 spec
- ✅ UI Mock 先行，後端就緒後接 API
- ✅ 最低支援 iOS 16.0
- ✅ MVVM + Repository 架構
- ✅ 不引入大型第三方依賴
- ✅ **App 名稱定案：「藥知道」**（Bundle ID: `com.mus2.drugrecognition`）
- ✅ **Apple Developer 帳號暫不申請**，採「模擬上架」呈現（截圖 + TestFlight 模擬流程展示）
- ✅ **競賽 deadline：6/30**
- ✅ **競賽範圍：Phase 0 + Phase 1 五大 MVP 模組全部完成**

---

## 8. 競賽衝刺排程（依 6/30 deadline 倒推）

> 距 deadline 約 5 週。**Phase 2/3/4 不在競賽範圍**，僅作為後續藍圖。

| 週次 | 重點 | 對應 Phase |
|---|---|---|
| W1（~6/2） | Xcode 專案建立、設計系統、Tab Bar、Mock 層、APIClient Protocol | P0 |
| W2（~6/9） | 藥品辨識原生化（相機 + 預處理 + 結果頁 + 歷史） | P1A |
| W3（~6/16） | 個人用藥管理 + 推播系統 | P1B + P1E |
| W4（~6/23） | 藥局地圖 + 安全警示 | P1C + P1D |
| W5（~6/30） | 整合測試、UI 拋光、Demo 影片、簡報、模擬上架素材 | 收尾 |

**關鍵風險點**：
- W2 相機橋接複雜，可能延誤 → 準備 fallback（PHPicker only）
- W3 推播需測試裝置（模擬器不支援 APNs）→ 提早確認測試機
- W5 留 1 週緩衝，**不安排新功能**

**競賽呈現策略**：
- App 內以 Mock 資料完整展示所有 5 大 MVP 流程
- 後端 API 串接列為 Phase 2 路線圖，向評審說明擴展性
- 模擬上架素材：App Store 截圖、宣傳影片、產品介紹頁

---

## 9. Capacitor 舊版處理

- 競賽期間 **保留** `ios/`（Swift 版進度落後時的 fallback）
- 6/30 競賽提交後：移至 `archive/capacitor-ios/` 或刪除
- `package.json` 的 `@capacitor/*` 依賴：競賽後一併清理
- **不在 Swift 版與 Capacitor 版同時開發**，避免分裂

---

## 10. 未決議題

- [x] 處方箋 OCR **進** MVP；PDF 匯出 **不做**
- [x] 採用 **Core Data**（iOS 16 相容）
- [x] App 內加「**Demo 模式**」切換，後端來不及時啟用，明確標示 Mock 資料
- [x] **錄製 Demo 影片**（W5）

---

## 11. Fallback 退路策略（多重備援）

> 競賽當天若新版出問題，可依序退守，確保仍能 demo。

| 層級 | 內容 | 觸發時機 | 操作 |
|---|---|---|---|
| **L1** | Swift 新版完整 demo（接後端 API）| 預設主推作品 | 正常啟動 |
| **L2** | Swift 新版 + Demo 模式（Mock 資料）| 後端 API 不穩 / 來不及 | App 內切換 Demo 模式 |
| **L3** | Capacitor `ios/` 舊版 demo | Swift 新版重大 bug | 切換另一台測試機 |
| **L4** | v2.0.2 tag 整包還原 | 全面退守（極端情況） | `git worktree add ../demo-v2.0.2 v2.0.2` |

**git tag 永久保存**：`v2.0.2` tag 是不可變的版本快照，任何時候都能取出。

**建議事前準備（W5 進行）**：
1. 預先建立 v2.0.2 demo worktree，確認能啟動
2. Capacitor `ios/` 版改 Bundle ID 為 `com.mus2.drugrecognition.legacy`，避免實機覆蓋 Swift 新版
3. 準備 demo 影片：Swift 新版主影片 + Capacitor 版備援影片
4. Demo 模式切換按鈕放在「我的」分頁顯眼處，方便現場切換

---

## 12. 立即下一步

1. ✅ 所有未決議題已確認
2. 本週啟動 W1：建立 Xcode 專案 + 設計系統
3. 鎖定一台 iPhone 實機作為推播測試裝置
4. 與後端開發者對齊：請優先完成 Auth + Medications + Safety API（影響 L1 能否實現）
