import XCTest
@testable import MUS_iOS

final class W2Tests: XCTestCase {

    func testMockAPIClientRecognizeDrugReturnsResult() async throws {
        let client = MockAPIClient()
        let data = Data([0x00, 0x01])
        let result = try await client.recognizeDrug(imageData: data)
        XCTAssertFalse(result.requestId.isEmpty)
        XCTAssertFalse(result.items.isEmpty)
    }

    @MainActor
    func testRecognitionHistoryStoreAppendAddsItem() {
        let store = RecognitionHistoryStore()
        let initialCount = store.records.count
        let result = RecognitionResult(requestId: "test-123", items: [
            RecognitionItem(drugId: 101, name: "普拿疼", confidence: 0.9)
        ])
        store.append(image: nil, result: result)
        XCTAssertEqual(store.records.count, initialCount + 1)
    }

    @MainActor
    func testRecognitionHistoryStoreDeleteRemovesItem() {
        let store = RecognitionHistoryStore()
        let result = RecognitionResult(requestId: "del-123", items: [
            RecognitionItem(drugId: 101, name: "普拿疼", confidence: 0.9)
        ])
        store.append(image: nil, result: result)
        let countAfterAdd = store.records.count
        store.delete(at: IndexSet(integer: 0))
        XCTAssertEqual(store.records.count, max(0, countAfterAdd - 1))
    }

    func testSafetyAlertLevelValues() {
        XCTAssertEqual(SafetyAlert.Level.major.rawValue, "major")
        XCTAssertEqual(SafetyAlert.Level.contraindicated.rawValue, "contraindicated")
        XCTAssertEqual(SafetyAlert.Level.moderate.rawValue, "moderate")
        XCTAssertEqual(SafetyAlert.Level.minor.rawValue, "minor")
    }
}
