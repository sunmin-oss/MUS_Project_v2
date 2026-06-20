import XCTest

final class AuthUITests: XCTestCase {
    var app: XCUIApplication!

    override func setUp() {
        super.setUp()
        continueAfterFailure = false
        app = XCUIApplication()
        app.launchArguments = ["--uitesting"]
        // NOTE: 不帶 --demo-mode，測試登入流程
    }

    // MARK: - Login Screen

    func testLoginScreenShowsAllElements() {
        app.launch()
        let usernameField = app.textFields["auth.username"]
        XCTAssertTrue(usernameField.waitForExistence(timeout: 10))
        XCTAssertTrue(app.secureTextFields["auth.password"].exists)
        XCTAssertTrue(app.buttons["auth.loginButton"].exists)
    }

    func testLoginButtonDisabledWhenEmpty() {
        app.launch()
        let loginButton = app.buttons["auth.loginButton"]
        XCTAssertTrue(loginButton.waitForExistence(timeout: 10))
        XCTAssertFalse(loginButton.isEnabled)
    }

    func testLoginButtonEnabledWhenFieldsFilled() {
        app.launch()
        let username = app.textFields["auth.username"]
        XCTAssertTrue(username.waitForExistence(timeout: 10))

        username.tap()
        username.typeText("demo")
        let password = app.secureTextFields["auth.password"]
        password.tap()
        password.typeText("Demo1234!")

        XCTAssertTrue(app.buttons["auth.loginButton"].isEnabled)
    }

    func testSuccessfulLoginShowsTabBar() {
        app.launch()
        let username = app.textFields["auth.username"]
        XCTAssertTrue(username.waitForExistence(timeout: 10))

        username.tap()
        username.typeText("demo")
        let password = app.secureTextFields["auth.password"]
        password.tap()
        password.typeText("Demo1234!")
        app.buttons["auth.loginButton"].tap()

        // 登入成功後應顯示 TabBar
        let tabBar = app.tabBars.firstMatch
        XCTAssertTrue(tabBar.waitForExistence(timeout: 15))
    }

    func testNavigateToRegisterView() {
        app.launch()
        let registerButton = app.buttons["立即註冊"]
        if registerButton.waitForExistence(timeout: 10) {
            registerButton.tap()
            XCTAssertTrue(app.textFields["register.username"].waitForExistence(timeout: 5))
            XCTAssertTrue(app.textFields["register.displayName"].exists)
            XCTAssertTrue(app.secureTextFields["register.password"].exists)
            XCTAssertTrue(app.secureTextFields["register.confirmPassword"].exists)
            XCTAssertTrue(app.buttons["register.submitButton"].exists)
        }
    }

    // MARK: - Demo Mode Auto-Login

    func testDemoModeSkipsLogin() {
        app.launchArguments = ["--uitesting", "--demo-mode"]
        app.launch()
        let tabBar = app.tabBars.firstMatch
        XCTAssertTrue(tabBar.waitForExistence(timeout: 5))
    }
}
