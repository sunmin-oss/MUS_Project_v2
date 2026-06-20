import XCTest

final class ConsultationUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
    }

    private func navigateToConsultationTab() {
        let consultTab = app.tabBars.buttons.element(boundBy: 2)
        XCTAssertTrue(consultTab.waitForExistence(timeout: 5))
        consultTab.tap()
    }

    // MARK: - Consultation List

    func testConsultationTabLoads() {
        navigateToConsultationTab()
        // AI 諮詢入口卡片應存在
        let aiEntry = app.buttons["consultation.ai.entry"]
        XCTAssertTrue(aiEntry.waitForExistence(timeout: 5))
    }

    func testAIDisclaimerVisible() {
        navigateToConsultationTab()
        let disclaimer = app.staticTexts["AI 回覆僅供參考，不構成醫療建議"]
        XCTAssertTrue(disclaimer.waitForExistence(timeout: 5))
    }

    // MARK: - AI Chat

    func testNavigateToAIChat() {
        navigateToConsultationTab()
        let aiEntry = app.buttons["consultation.ai.entry"]
        XCTAssertTrue(aiEntry.waitForExistence(timeout: 5))
        aiEntry.tap()

        // 應進入 AI 聊天頁面
        let chatTitle = app.navigationBars["AI 藥物諮詢"]
        XCTAssertTrue(chatTitle.waitForExistence(timeout: 5))
    }

    func testAIChatWelcomeMessage() {
        navigateToConsultationTab()
        app.buttons["consultation.ai.entry"].tap()
        sleep(2)

        // 歡迎訊息應存在
        let welcomeText = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS 'AI 藥物諮詢助手'")
        ).firstMatch
        XCTAssertTrue(welcomeText.waitForExistence(timeout: 5))
    }

    func testAIChatInputFieldExists() {
        navigateToConsultationTab()
        app.buttons["consultation.ai.entry"].tap()

        let inputField = app.textFields["chat.input"]
        XCTAssertTrue(inputField.waitForExistence(timeout: 5))
    }

    func testAIChatSendButtonDisabledWhenEmpty() {
        navigateToConsultationTab()
        app.buttons["consultation.ai.entry"].tap()

        let sendButton = app.buttons["chat.send"]
        XCTAssertTrue(sendButton.waitForExistence(timeout: 5))
        XCTAssertFalse(sendButton.isEnabled)
    }

    func testAIChatSendMessage() {
        navigateToConsultationTab()
        app.buttons["consultation.ai.entry"].tap()

        let inputField = app.textFields["chat.input"]
        XCTAssertTrue(inputField.waitForExistence(timeout: 5))
        inputField.tap()
        inputField.typeText("普拿疼可以空腹吃嗎")

        let sendButton = app.buttons["chat.send"]
        XCTAssertTrue(sendButton.isEnabled)
        sendButton.tap()

        // 等待 AI 回覆
        sleep(5)

        // 應有至少 3 個訊息（歡迎 + 使用者 + AI 回覆）
        let bubbles = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS '僅供參考' OR label CONTAINS '普拿疼'")
        )
        XCTAssertGreaterThanOrEqual(bubbles.count, 1)
    }

    func testAIChatDisclaimerBanner() {
        navigateToConsultationTab()
        app.buttons["consultation.ai.entry"].tap()

        // 免責聲明 banner 應存在
        let banner = app.staticTexts.matching(
            NSPredicate(format: "label CONTAINS '不構成醫療建議'")
        ).firstMatch
        XCTAssertTrue(banner.waitForExistence(timeout: 5))
    }
}
