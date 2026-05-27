import XCTest

final class MedicationUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
    }

    func testMedicationTabShowsMedicationsListView() {
        let medTab = app.tabBars.buttons.element(boundBy: 1)
        if medTab.waitForExistence(timeout: 5) {
            medTab.tap()
            let navTitle = app.navigationBars["我的用藥"].firstMatch
            XCTAssertTrue(navTitle.waitForExistence(timeout: 5))
        }
    }

    func testProfileSwitcherShowsAtLeastOneChip() {
        let medTab = app.tabBars.buttons.element(boundBy: 1)
        if medTab.waitForExistence(timeout: 5) {
            medTab.tap()
            let chip = app.buttons["我本人"].firstMatch
            XCTAssertTrue(chip.waitForExistence(timeout: 5))
        }
    }

    func testAddButtonShowsAddMedicationView() {
        let medTab = app.tabBars.buttons.element(boundBy: 1)
        if medTab.waitForExistence(timeout: 5) {
            medTab.tap()
        }
        let addButton = app.navigationBars.buttons["medications.add.title"].firstMatch
        if addButton.waitForExistence(timeout: 5) {
            addButton.tap()
            let form = app.navigationBars["新增用藥"].firstMatch
            XCTAssertTrue(form.waitForExistence(timeout: 5))
        }
    }
}
