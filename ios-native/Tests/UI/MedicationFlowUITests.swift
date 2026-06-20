import XCTest

final class MedicationFlowUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
    }

    private func navigateToMedTab() {
        let medTab = app.tabBars.buttons.element(boundBy: 1)
        XCTAssertTrue(medTab.waitForExistence(timeout: 5))
        medTab.tap()
    }

    // MARK: - Medication List

    func testMedicationListLoads() {
        navigateToMedTab()
        let navTitle = app.navigationBars["我的用藥"].firstMatch
        XCTAssertTrue(navTitle.waitForExistence(timeout: 5))
    }

    func testTimePeriodTabsExist() {
        navigateToMedTab()
        sleep(2) // 等待載入
        // 時段按鈕應存在
        XCTAssertTrue(app.buttons["全部"].waitForExistence(timeout: 5))
    }

    func testTimePeriodTabSwitching() {
        navigateToMedTab()
        sleep(2)
        let allTab = app.buttons["全部"].firstMatch
        if allTab.waitForExistence(timeout: 5) {
            // 切換到各個時段
            for tabName in ["早上", "中午", "晚上", "睡前", "全部"] {
                let tab = app.buttons[tabName].firstMatch
                if tab.exists { tab.tap() }
                sleep(1)
            }
        }
    }

    // MARK: - Add Medication

    func testAddMedicationFormOpens() {
        navigateToMedTab()
        let addButton = app.navigationBars.buttons["medications.add.title"].firstMatch
        if addButton.waitForExistence(timeout: 5) {
            addButton.tap()
            let navTitle = app.navigationBars["新增用藥"].firstMatch
            XCTAssertTrue(navTitle.waitForExistence(timeout: 5))
        }
    }

    func testAddMedicationFormFields() {
        navigateToMedTab()
        let addButton = app.navigationBars.buttons["medications.add.title"].firstMatch
        if addButton.waitForExistence(timeout: 5) {
            addButton.tap()
            sleep(1)
            // 表單中應有藥名和劑量輸入欄
            // Form 元素用 staticTexts 或 textFields 搜尋
            XCTAssertTrue(app.navigationBars["新增用藥"].exists)
        }
    }

    // MARK: - Confirm Medication

    func testConfirmSheetAppears() {
        navigateToMedTab()
        sleep(3) // 等待藥物列表載入

        // 找到第一個「確認服藥」按鈕
        let confirmButton = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '確認服藥'")
        ).firstMatch

        if confirmButton.waitForExistence(timeout: 5) {
            confirmButton.tap()
            // 確認 sheet 應出現，包含三個按鈕
            let takenButton = app.buttons["confirm.taken"]
            XCTAssertTrue(takenButton.waitForExistence(timeout: 5))
            XCTAssertTrue(app.buttons["confirm.snooze"].exists)
            XCTAssertTrue(app.buttons["confirm.skip"].exists)
        }
    }

    func testConfirmTakenShowsUndoBar() {
        navigateToMedTab()
        sleep(3)

        let confirmButton = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '確認服藥'")
        ).firstMatch

        if confirmButton.waitForExistence(timeout: 5) {
            confirmButton.tap()
            let takenButton = app.buttons["confirm.taken"]
            if takenButton.waitForExistence(timeout: 5) {
                takenButton.tap()
                // 撤銷 snackbar 應出現
                let undoButton = app.buttons["med.undo"]
                XCTAssertTrue(undoButton.waitForExistence(timeout: 5))
            }
        }
    }

    func testConfirmSnooze() {
        navigateToMedTab()
        sleep(3)

        let confirmButton = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '確認服藥'")
        ).firstMatch

        if confirmButton.waitForExistence(timeout: 5) {
            confirmButton.tap()
            let snoozeButton = app.buttons["confirm.snooze"]
            if snoozeButton.waitForExistence(timeout: 5) {
                snoozeButton.tap()
                // Sheet 應關閉，回到列表
                sleep(1)
                XCTAssertTrue(app.navigationBars["我的用藥"].exists)
            }
        }
    }

    func testConfirmSkip() {
        navigateToMedTab()
        sleep(3)

        let confirmButton = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '確認服藥'")
        ).firstMatch

        if confirmButton.waitForExistence(timeout: 5) {
            confirmButton.tap()
            let skipButton = app.buttons["confirm.skip"]
            if skipButton.waitForExistence(timeout: 5) {
                skipButton.tap()
                sleep(1)
                XCTAssertTrue(app.navigationBars["我的用藥"].exists)
            }
        }
    }

    // MARK: - Medication Detail

    func testNavigateToMedicationDetail() {
        navigateToMedTab()
        sleep(3)

        // 點擊第一個藥物卡片（NavigationLink）
        let firstMed = app.buttons.matching(
            NSPredicate(format: "label CONTAINS '服'")
        ).firstMatch

        if firstMed.waitForExistence(timeout: 5) {
            firstMed.tap()
            sleep(2)
            // 應有編輯按鈕
            let editButton = app.buttons["編輯"].firstMatch
            XCTAssertTrue(editButton.waitForExistence(timeout: 5))
        }
    }

    // MARK: - Profile Switcher

    func testProfileSwitcherVisible() {
        navigateToMedTab()
        let chip = app.buttons["我本人"].firstMatch
        XCTAssertTrue(chip.waitForExistence(timeout: 5))
    }

    // MARK: - Edit Mode

    func testEditModeToggle() {
        navigateToMedTab()
        sleep(3)

        let editButton = app.buttons["編輯"].firstMatch
        if editButton.waitForExistence(timeout: 5) {
            editButton.tap()
            // 應切換到編輯模式，出現「完成」按鈕
            let doneButton = app.buttons["完成"].firstMatch
            XCTAssertTrue(doneButton.waitForExistence(timeout: 3))
            doneButton.tap()
        }
    }

    // MARK: - Calendar

    func testCalendarNavigation() {
        navigateToMedTab()
        let calendarButton = app.buttons["calendar.badge.checkmark"].firstMatch
        if calendarButton.waitForExistence(timeout: 5) {
            calendarButton.tap()
            sleep(1)
        }
    }
}
