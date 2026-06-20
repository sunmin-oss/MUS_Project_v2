import XCTest

/// 論文截圖專用測試 — 自動導航到各功能頁面並儲存截圖
/// 執行方式：xcodebuild test -project MUS-iOS.xcodeproj -scheme MUS-iOS \
///   -destination 'platform=iOS Simulator,name=iPhone 16' \
///   -only-testing MUS-iOSUITests/ThesisScreenshotTests
final class ThesisScreenshotTests: XCTestCase {
    
    let app = XCUIApplication()
    let saveDir = "/Users/sunmin/Desktop/MUS_Project_v2/論文/圖表/系統截圖/iOS"
    
    override func setUpWithError() throws {
        continueAfterFailure = true
        app.launchArguments += ["--uitesting", "--demo-mode"]
        app.launch()
        sleep(2) // 等待 App 完全載入
    }
    
    // MARK: - Helper
    
    func saveScreenshot(name: String) {
        let screenshot = app.screenshot()
        let data = screenshot.pngRepresentation
        let url = URL(fileURLWithPath: saveDir).appendingPathComponent(name)
        try? data.write(to: url)
        
        // 也加入 XCTest attachment 以備查看
        let attachment = XCTAttachment(screenshot: screenshot)
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
    
    // MARK: - 截圖測試
    
    func test01_首頁() throws {
        // 確保在首頁 Tab
        let homeTab = app.tabBars.buttons["首頁"]
        if homeTab.exists { homeTab.tap() }
        sleep(1)
        saveScreenshot(name: "SS-iOS-01_首頁.png")
    }
    
    func test02_用藥清單() throws {
        let medsTab = app.tabBars.buttons["我的用藥"]
        XCTAssertTrue(medsTab.waitForExistence(timeout: 5))
        medsTab.tap()
        sleep(1)
        saveScreenshot(name: "SS-iOS-02_用藥清單.png")
    }
    
    func test03_藥師諮詢() throws {
        let consultTab = app.tabBars.buttons["藥師諮詢"]
        XCTAssertTrue(consultTab.waitForExistence(timeout: 5))
        consultTab.tap()
        sleep(1)
        saveScreenshot(name: "SS-iOS-03_藥師諮詢.png")
    }
    
    func test04_諮詢AI對話() throws {
        let consultTab = app.tabBars.buttons["藥師諮詢"]
        if consultTab.exists { consultTab.tap() }
        sleep(1)
        
        // 嘗試進入 AI 對話
        let aiEntry = app.buttons["consultation.ai.entry"]
        if aiEntry.waitForExistence(timeout: 3) {
            aiEntry.tap()
            sleep(1)
            saveScreenshot(name: "SS-iOS-04_AI諮詢對話.png")
            // 返回
            app.navigationBars.buttons.firstMatch.tap()
        } else {
            // 如果找不到，直接截目前畫面
            saveScreenshot(name: "SS-iOS-04_AI諮詢對話.png")
        }
    }
    
    func test05_個人設定() throws {
        let profileTab = app.tabBars.buttons["我的"]
        XCTAssertTrue(profileTab.waitForExistence(timeout: 5))
        profileTab.tap()
        sleep(1)
        saveScreenshot(name: "SS-iOS-05_個人設定.png")
    }
    
    func test06_搜尋藥物() throws {
        // 回到首頁
        let homeTab = app.tabBars.buttons["首頁"]
        if homeTab.exists { homeTab.tap() }
        sleep(1)
        
        // 點擊搜尋
        let searchButton = app.buttons["搜尋藥物名稱"]
        if searchButton.waitForExistence(timeout: 3) {
            searchButton.tap()
            sleep(1)
            saveScreenshot(name: "SS-iOS-06_藥物搜尋.png")
        } else {
            // fallback: 嘗試其他標識
            let searchAlt = app.buttons.matching(NSPredicate(format: "label CONTAINS '搜尋'")).firstMatch
            if searchAlt.exists {
                searchAlt.tap()
                sleep(1)
            }
            saveScreenshot(name: "SS-iOS-06_藥物搜尋.png")
        }
    }
    
    func test07_辨識功能() throws {
        let homeTab = app.tabBars.buttons["首頁"]
        if homeTab.exists { homeTab.tap() }
        sleep(1)
        
        // 點擊拍照辨識
        let recognizeButton = app.buttons["拍照辨識藥物"]
        if recognizeButton.waitForExistence(timeout: 3) {
            recognizeButton.tap()
            sleep(1)
            saveScreenshot(name: "SS-iOS-07_拍照辨識.png")
        } else {
            saveScreenshot(name: "SS-iOS-07_拍照辨識.png")
        }
    }
    
    func test08_用藥管理_時段篩選() throws {
        let medsTab = app.tabBars.buttons["我的用藥"]
        if medsTab.exists { medsTab.tap() }
        sleep(1)
        
        // 點擊不同時段 tab（如果有的話）
        let afternoonTab = app.buttons["下午"]
        if afternoonTab.waitForExistence(timeout: 2) {
            afternoonTab.tap()
            sleep(1)
        }
        saveScreenshot(name: "SS-iOS-08_用藥時段篩選.png")
    }
}
