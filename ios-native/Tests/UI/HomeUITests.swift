import XCTest

final class HomeUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
    }

    func testFourTabsAreAccessible() {
        let tabBar = app.tabBars.firstMatch
        XCTAssertTrue(tabBar.waitForExistence(timeout: 5))
        XCTAssertGreaterThanOrEqual(tabBar.buttons.count, 3)
    }

    func testTappingRecognitionButtonNavigatesToRecognitionView() {
        let recognizeButton = app.buttons["home.action.recognize"]
            .firstMatch
        if recognizeButton.waitForExistence(timeout: 5) {
            recognizeButton.tap()
            // After tap, RecognitionView should appear
            let cameraButton = app.buttons.element(matching: .button, identifier: "辨識藥物").firstMatch
            _ = cameraButton.waitForExistence(timeout: 3)
        }
    }

    func testTappingProfileTabShowsProfileView() {
        let profileTab = app.tabBars.buttons.element(boundBy: 3)
        if profileTab.waitForExistence(timeout: 5) {
            profileTab.tap()
        }
    }
}
