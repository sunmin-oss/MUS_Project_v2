# MUS-iOS (藥知道 SwiftUI 原生 App)

W1 骨架：對應 `docs/APP_ROADMAP.md` Phase 0（P0.1–P0.7）

## 快速開始

```bash
brew install xcodegen        # 一次性
cd ios-native
xcodegen generate            # 產生 MUS-iOS.xcodeproj
open MUS-iOS.xcodeproj       # 用 Xcode 16.4+ 開啟
```

## 結構

```
ios-native/
├─ project.yml               # XcodeGen 專案描述
└─ MUS-iOS/
   ├─ App/                   # MUSApp、AppEnvironment(DI)、RootView(TabBar)
   ├─ Core/
   │  ├─ Network/            # APIClient Protocol、RealAPIClient（Phase 3 補完）
   │  └─ Storage/Models.swift
   ├─ DesignSystem/          # Colors、Typography、Spacing、共用元件
   ├─ Features/              # Home / Medications / Consultation / Profile（其餘 Phase 1+ 補上）
   ├─ Mocks/                 # MockAPIClient + MockData
   └─ Resources/             # Info.plist、Localizable.xcstrings、Assets.xcassets
```

## 切換 Mock / Real API

`AppEnvironment.makeDefault()` 內注入 `MockAPIClient`；Phase 3 後端就緒後改為 `RealAPIClient(baseURL:)` 即可。
使用者亦可在「我的」分頁切換 **Demo 模式**（影響 UI 上方的展示模式 banner）。

## 進度追蹤

W1 任務列表詳見 `docs/APP_ROADMAP.md` §8。
