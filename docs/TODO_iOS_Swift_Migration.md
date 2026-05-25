# TODO: iOS 原生 Swift 遷移（方案 B）

> **目標**：將現有 Capacitor 封裝替換為自行開發的 Swift 原生殼，符合競賽「鼓勵使用 Xcode + Swift」的要求。
> 
> **策略**：混合架構 — 用 Swift 原生實作「相機拍照」等硬體功能，其餘 UI 透過 `WKWebView` 載入現有 SPA 前端。
> 
> **預計工作量**：中等（約 2-3 天），核心前端邏輯無需修改。

---

## 背景

競賽規則：
> 鼓勵參賽隊伍下載 Xcode 並且使用 Swift 語言進行開發。

目前做法：使用 Capacitor 將 `index.html` SPA 包進 WebView 容器 → iOS App  
目標做法：用 Swift 原生建立 App 殼，自行內嵌 `WKWebView`，相機功能用原生 Swift 實作

---

## 任務清單

### 1. 建立新的 Swift 原生專案
- [ ] 在 Xcode 建立新的 iOS App 專案（Swift + UIKit 或 SwiftUI）
- [ ] App Bundle ID：`com.mus2.drugrecognition`（沿用）
- [ ] App 名稱：`藥知道`
- [ ] 部署目標：iOS 16.0+
- [ ] 新專案路徑：`ios-native/` （與原 `ios/` Capacitor 版共存）

### 2. WKWebView 整合
- [ ] 建立主畫面，內嵌 `WKWebView`
- [ ] 設定載入後端 URL（`http://<SERVER_IP>:5000/`）或本地 `index.html`
- [ ] 設定 `WKWebViewConfiguration`：允許 JavaScript、inline media playback
- [ ] 處理 `WKNavigationDelegate` 錯誤回調（網路斷線提示）
- [ ] 設定 App Transport Security (ATS) 允許 HTTP 連線（開發用）

### 3. 原生相機功能（重點）
- [ ] 用 `UIImagePickerController` 或 `PHPickerViewController` 實作拍照/選照片
- [ ] 建立 Swift ↔ JavaScript 橋接：
  - JS 端呼叫 `window.webkit.messageHandlers.camera.postMessage("takePhoto")`
  - Swift 端透過 `WKScriptMessageHandler` 接收訊息
  - 拍照完成後將圖片 Base64 注入回 WebView：`webView.evaluateJavaScript("receivePhoto('\(base64)')")`
- [ ] 前端 `index.html` 需新增判斷：如果是原生 App 環境，改用橋接拍照而非 `<input type="file">`

### 4. 前端適配修改
- [ ] 在 `index.html` 新增環境偵測：

```javascript
// 偵測是否為 Swift 原生 App 環境
const isNativeApp = window.webkit && window.webkit.messageHandlers && window.webkit.messageHandlers.camera;

// 拍照按鈕改為：
if (isNativeApp) {
    window.webkit.messageHandlers.camera.postMessage("takePhoto");
} else {
    // 原有的 <input type="file"> 流程
}

// 接收原生相機回傳的照片
function receivePhoto(base64Data) {
    // 將 base64 圖片送去辨識 API
}
```

### 5. iOS App 設定
- [ ] 設定 `Info.plist`：
  - `NSCameraUsageDescription`：「藥知道需要使用相機拍攝藥物照片進行辨識」
  - `NSPhotoLibraryUsageDescription`：「藥知道需要存取相簿選取藥物照片」
- [ ] 設定 App Icon（沿用現有圖示）
- [ ] 設定 Launch Screen

### 6. 測試
- [ ] 在 iOS 模擬器測試 WebView 載入
- [ ] 在實體 iPhone 測試原生相機拍照 → 辨識流程
- [ ] 測試藥單 OCR 模式（相機 → 辨識處方箋）
- [ ] 測試名稱搜尋模式（純 WebView 操作）
- [ ] 測試日/夜間模式切換
- [ ] 測試網路斷線錯誤處理

### 7. 清理與文件
- [ ] 移除 Capacitor 相關依賴（`capacitor.config.json`、`ios/` 舊目錄）
- [ ] 更新企畫書技術描述：Capacitor → Swift + WKWebView
- [ ] 更新 README.md iOS 章節

---

## 關鍵程式碼參考

### Swift 端 — ViewController.swift（骨架）

```swift
import UIKit
import WebKit

class ViewController: UIViewController, WKScriptMessageHandler, WKNavigationDelegate, UIImagePickerControllerDelegate, UINavigationControllerDelegate {
    
    var webView: WKWebView!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // 設定 WKWebView
        let config = WKWebViewConfiguration()
        config.userContentController.add(self, name: "camera")
        config.allowsInlineMediaPlayback = true
        
        webView = WKWebView(frame: view.bounds, configuration: config)
        webView.navigationDelegate = self
        webView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        view.addSubview(webView)
        
        // 載入後端頁面
        if let url = URL(string: "http://YOUR_SERVER_IP:5000/") {
            webView.load(URLRequest(url: url))
        }
    }
    
    // JS → Swift 橋接：接收拍照請求
    func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
        if message.name == "camera" {
            openCamera()
        }
    }
    
    // 開啟原生相機
    func openCamera() {
        let picker = UIImagePickerController()
        picker.delegate = self
        picker.sourceType = .camera
        present(picker, animated: true)
    }
    
    // 拍照完成 → Base64 → 回傳給 WebView
    func imagePickerController(_ picker: UIImagePickerController, didFinishPickingMediaWithInfo info: [UIImagePickerController.InfoKey : Any]) {
        picker.dismiss(animated: true)
        if let image = info[.originalImage] as? UIImage,
           let data = image.jpegData(compressionQuality: 0.8) {
            let base64 = data.base64EncodedString()
            webView.evaluateJavaScript("receivePhoto('\(base64)')") 
        }
    }
}
```

---

## 現有 Capacitor 設定（供參考）

```json
{
  "appId": "com.mus2.drugrecognition",
  "appName": "藥知道",
  "webDir": "www",
  "server": {
    "allowNavigation": ["192.168.1.103:5000", "*.192.168.1.103"]
  }
}
```

---

## 注意事項

- 需在 **macOS + Xcode 15+** 環境開發
- 實機測試需 Apple Developer 帳號（免費版可側載到自己的裝置）
- `WKWebView` 載入 HTTP (非 HTTPS) 需在 Info.plist 設定 ATS 例外
- 完成後企畫書可改寫為：「使用 **Swift + Xcode** 開發 iOS 原生應用，前端採 WKWebView 混合架構」
