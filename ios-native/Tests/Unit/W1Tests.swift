import XCTest
@testable import MUS_iOS

final class W1Tests: XCTestCase {

    @MainActor
    func testFontScalePersistsToUserDefaults() {
        let settings = AppSettings()
        settings.fontScale = .large
        XCTAssertEqual(UserDefaults.standard.string(forKey: "appSettings.fontScale"), "large")
        settings.fontScale = .normal
    }

    @MainActor
    func testThemePersistsToUserDefaults() {
        let settings = AppSettings()
        settings.theme = .warm
        XCTAssertEqual(UserDefaults.standard.string(forKey: "appSettings.theme"), "warm")
        settings.theme = .system
    }

    func testMockProfilesNotEmpty() {
        XCTAssertFalse(MockData.profiles.isEmpty)
    }

    func testMockDrugsCountAtLeastThree() {
        XCTAssertGreaterThanOrEqual(MockData.drugs.count, 3)
    }

    func testLocalizableXcstringsIsValidJSON() throws {
        guard let url = Bundle.main.url(forResource: "Localizable", withExtension: "xcstrings") else {
            throw XCTSkip("Localizable.xcstrings not found in test bundle")
        }
        let data = try Data(contentsOf: url)
        XCTAssertNoThrow(try JSONSerialization.jsonObject(with: data))
    }
}
