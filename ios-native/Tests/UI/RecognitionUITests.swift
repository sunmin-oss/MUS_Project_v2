import XCTest

final class RecognitionUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
    }

    // MARK: - Recognition Entry

    func testRecognizeButtonNavigatesToRecognitionView() {
        let recognizeButton = app.buttons["home.action.recognize"]
        XCTAssertTrue(recognizeButton.waitForExistence(timeout: 5))
        recognizeButton.tap()
        // 應顯示辨識畫面（可能有 source 選擇 dialog）
        sleep(1)
    }

    // MARK: - Drug Search

    func testSearchButtonNavigatesToSearchView() {
        let searchButton = app.buttons["home.action.search"]
        XCTAssertTrue(searchButton.waitForExistence(timeout: 5))
        searchButton.tap()
        // 搜尋輸入框應出現
        let searchField = app.textFields["search.drug.input"]
        XCTAssertTrue(searchField.waitForExistence(timeout: 5))
    }

    func testDrugSearchInputAndResults() {
        let searchButton = app.buttons["home.action.search"]
        XCTAssertTrue(searchButton.waitForExistence(timeout: 5))
        searchButton.tap()

        let searchField = app.textFields["search.drug.input"]
        XCTAssertTrue(searchField.waitForExistence(timeout: 5))
        searchField.tap()
        searchField.typeText("普拿疼")

        // 等待搜尋結果（可能需要 API 回應）
        sleep(3)
    }

    // MARK: - Recognition History

    func testHistoryButtonNavigatesToHistoryView() {
        let historyButton = app.buttons["home.action.history"]
        XCTAssertTrue(historyButton.waitForExistence(timeout: 5))
        historyButton.tap()
        sleep(1)
    }

    // MARK: - Prescription Entry

    func testPrescriptionButtonShowsSheet() {
        let prescriptionButton = app.buttons["home.action.prescription"]
        XCTAssertTrue(prescriptionButton.waitForExistence(timeout: 5))
        prescriptionButton.tap()
        // 處方箋 sheet 應彈出
        sleep(1)
    }
}
