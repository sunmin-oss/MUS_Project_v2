import XCTest

final class PharmacyUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
    }

    func testPharmacyMapViewLoads() {
        // Navigate to pharmacy from home
        let pharmacyButton = app.buttons["home.action.pharmacy"].firstMatch
        if pharmacyButton.waitForExistence(timeout: 5) {
            pharmacyButton.tap()
            let navTitle = app.navigationBars["附近藥局"].firstMatch
            XCTAssertTrue(navTitle.waitForExistence(timeout: 5))
        }
    }

    func testPharmacyListSegmentedControl() {
        let pharmacyButton = app.buttons["home.action.pharmacy"].firstMatch
        if pharmacyButton.waitForExistence(timeout: 5) {
            pharmacyButton.tap()
            let listButton = app.buttons["列表"].firstMatch
            if listButton.waitForExistence(timeout: 3) {
                listButton.tap()
            }
        }
    }
}
