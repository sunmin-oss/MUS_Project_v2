import XCTest
@testable import MUS_iOS

final class W4Tests: XCTestCase {

    // PharmacyStore filter: filterNHI=true returns only NHS pharmacies
    @MainActor
    func testPharmacyStoreFilterNHI() async {
        let store = PharmacyStore()
        let client = MockAPIClient()
        await store.load(latitude: 25.04, longitude: 121.51, apiClient: client)
        store.filterNHI = true
        XCTAssertTrue(store.filtered.allSatisfy { $0.isNHIContracted })
    }

    // PharmacyStore filter: filter24h=true returns only 24h pharmacies
    @MainActor
    func testPharmacyStoreFilter24h() async {
        let store = PharmacyStore()
        let client = MockAPIClient()
        await store.load(latitude: 25.04, longitude: 121.51, apiClient: client)
        store.filter24h = true
        XCTAssertTrue(store.filtered.allSatisfy { $0.is24h })
    }

    // PharmacyStore favorites toggle
    @MainActor
    func testPharmacyStoreFavoriteToggle() {
        let store = PharmacyStore()
        XCTAssertFalse(store.isFavorite("ph1"))
        store.toggleFavorite("ph1")
        XCTAssertTrue(store.isFavorite("ph1"))
        store.toggleFavorite("ph1")
        XCTAssertFalse(store.isFavorite("ph1"))
    }

    // AllergyStore add increases count
    @MainActor
    func testAllergyStoreAddIncreasesCount() async throws {
        let store = AllergyStore()
        let client = MockAPIClient()
        await store.load(profileId: "p1", apiClient: client)
        let initial = store.items.count
        try await store.add(name: "測試過敏", profileId: "p1", apiClient: client)
        XCTAssertEqual(store.items.count, initial + 1)
    }

    // SafetyAlert level colors (test the raw values match expected strings)
    func testSafetyAlertLevelMapping() {
        XCTAssertEqual(SafetyAlert.Level.contraindicated.rawValue, "contraindicated")
        XCTAssertEqual(SafetyAlert.Level.major.rawValue, "major")
        XCTAssertEqual(SafetyAlert.Level.moderate.rawValue, "moderate")
        XCTAssertEqual(SafetyAlert.Level.minor.rawValue, "minor")
    }
}
