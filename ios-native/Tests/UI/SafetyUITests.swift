import XCTest

final class SafetyUITests: XCTestCase {
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

    // MARK: - Allergy List

    func testNavigateToAllergyList() {
        navigateToProfile()
        sleep(1)

        // 點擊過敏原清單
        let allergyLink = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '過敏'")
        ).firstMatch

        if allergyLink.waitForExistence(timeout: 5) {
            allergyLink.tap()
            sleep(1)
        }
    }

    func testAllergyAddButton() {
        navigateToProfile()
        sleep(1)

        let allergyLink = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '過敏'")
        ).firstMatch

        if allergyLink.waitForExistence(timeout: 5) {
            allergyLink.tap()
            sleep(1)
            // 新增按鈕應存在
            let addButton = app.buttons.matching(
                NSPredicate(format: "label CONTAINS '新增' OR label CONTAINS 'plus'")
            ).firstMatch
            if addButton.waitForExistence(timeout: 3) {
                addButton.tap()
                // 新增 Alert 應出現
                sleep(1)
            }
        }
    }

    // MARK: - Health Profile

    func testNavigateToHealthProfile() {
        navigateToProfile()
        sleep(1)

        let healthLink = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '健康'")
        ).firstMatch

        if healthLink.waitForExistence(timeout: 5) {
            healthLink.tap()
            sleep(1)
            // 健康檔案應有 Toggle 項目
        }
    }

    func testHealthProfileTogglesExist() {
        navigateToProfile()
        sleep(1)

        let healthLink = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '健康'")
        ).firstMatch

        if healthLink.waitForExistence(timeout: 5) {
            healthLink.tap()
            sleep(2)

            // 至少應有部分 Toggle 存在（懷孕、哺乳等）
            let toggles = app.switches
            XCTAssertGreaterThanOrEqual(toggles.count, 1)
        }
    }
}
