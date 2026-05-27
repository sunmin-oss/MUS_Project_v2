import XCTest
@testable import MUS_iOS

final class W3Tests: XCTestCase {

    @MainActor
    func testMedicationStoreAddIncreasesCount() async throws {
        let store = MedicationStore()
        let client = MockAPIClient()
        await store.load(profileId: "p1", apiClient: client)
        let initial = store.medications.count
        let newMed = Medication(
            id: UUID().uuidString, profileId: "p1", drugName: "測試藥",
            dosage: "1 顆", frequency: "每日一次", mealTiming: "飯後",
            nextDoseAt: Date(), currentStock: 10, reminderTimes: [], notes: ""
        )
        try await store.add(medication: newMed, apiClient: client)
        XCTAssertEqual(store.medications.count, initial + 1)
    }

    @MainActor
    func testMedicationStoreDeleteDecreasesCount() async throws {
        let store = MedicationStore()
        let client = MockAPIClient()
        await store.load(profileId: "p1", apiClient: client)
        guard let firstId = store.medications.first?.id else {
            throw XCTSkip("No medications to delete")
        }
        let countBefore = store.medications.count
        try await store.delete(id: firstId, apiClient: client)
        XCTAssertEqual(store.medications.count, countBefore - 1)
    }

    @MainActor
    func testRecordTakenCreatesTakenRecord() async {
        let store = MedicationStore()
        await store.recordTaken(medicationId: "m1", profileId: "p1")
        XCTAssertTrue(store.records.contains { $0.medicationId == "m1" && $0.status == .taken })
    }

    @MainActor
    func testAdherenceRateInRange() async {
        let store = MedicationStore()
        let client = MockAPIClient()
        await store.load(profileId: "p1", apiClient: client)
        let rate = store.adherenceRate(medicationId: "m1", days: 7)
        XCTAssertGreaterThanOrEqual(rate, 0.0)
        XCTAssertLessThanOrEqual(rate, 1.0)
    }

    @MainActor
    func testRecordsByDayReturnsCorrectBuckets() async {
        let store = MedicationStore()
        let client = MockAPIClient()
        await store.load(profileId: "p1", apiClient: client)
        let days = store.recordsByDay(medicationId: nil, days: 7)
        XCTAssertEqual(days.count, 7)
    }

    func testNotificationManagerSharedNotNil() {
        XCTAssertNotNil(NotificationManager.shared)
    }
}
