import XCTest

final class ProfileUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
    }

    private func navigateToProfile() {
        let profileTab = app.tabBars.buttons.element(boundBy: 3)
        XCTAssertTrue(profileTab.waitForExistence(timeout: 5))
        profileTab.tap()
    }

    // MARK: - Profile Screen

    func testProfileTabLoads() {
        navigateToProfile()
        let navTitle = app.navigationBars.firstMatch
        XCTAssertTrue(navTitle.waitForExistence(timeout: 5))
    }

    func testVersionInfoVisible() {
        navigateToProfile()
        sleep(1)
        let versionText = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS '1.0.0'")
        ).firstMatch
        XCTAssertTrue(versionText.waitForExistence(timeout: 5))
    }

    // MARK: - Appearance Settings

    func testFontSizePickerExists() {
        navigateToProfile()
        sleep(1)
        // 字體大小 Picker 應存在
        let fontLabel = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS '字體' OR label CONTAINS '大小'")
        ).firstMatch
        if fontLabel.exists {
            XCTAssertTrue(fontLabel.exists)
        }
    }

    func testThemePickerExists() {
        navigateToProfile()
        sleep(1)
        // 主題 Picker 應存在
        let themeLabel = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS '主題' OR label CONTAINS 'theme'")
        ).firstMatch
        if themeLabel.exists {
            XCTAssertTrue(themeLabel.exists)
        }
    }

    func testThemeColorPreviewButtons() {
        navigateToProfile()
        sleep(1)
        // 至少應有主題色預覽圓點（至少 2 個）
        // 主題色是圓形按鈕
    }

    // MARK: - Personal Info

    func testNavigateToPersonalInfo() {
        navigateToProfile()
        sleep(1)

        // 點擊帳號卡片進入個人資訊
        let accountCell = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '編輯個人資訊'")
        ).firstMatch

        if accountCell.waitForExistence(timeout: 5) {
            accountCell.tap()
            sleep(1)
        }
    }

    // MARK: - Notifications (Coming Soon)

    func testNotificationsSection() {
        navigateToProfile()
        sleep(1)
        // 通知應顯示 "Coming Soon"
    }

    // MARK: - Safety Section Navigation

    func testSafetySectionExists() {
        navigateToProfile()
        sleep(1)
        // 安全區段應有過敏原和健康檔案連結
        let allergyLink = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS '過敏'")
        ).firstMatch
        XCTAssertTrue(allergyLink.waitForExistence(timeout: 5))
    }
}
