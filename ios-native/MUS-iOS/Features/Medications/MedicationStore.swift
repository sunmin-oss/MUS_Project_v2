import Foundation

@MainActor
final class MedicationStore: ObservableObject {
    @Published var medications: [Medication] = []
    @Published var records: [MedicationRecord] = []
    @Published var lastTakenRecord: MedicationRecord?

    private func cacheKey(_ profileId: String) -> String { "medications_\(profileId)" }
    private func recordsCacheKey(_ profileId: String) -> String { "med_records_\(profileId)" }

    func load(profileId: String, apiClient: APIClientProtocol) async {
        // 先載入快取作為初始資料
        if medications.isEmpty, let cached = LocalCache.load([Medication].self, forKey: cacheKey(profileId)) {
            medications = cached
        }
        if records.isEmpty, let cached = LocalCache.load([MedicationRecord].self, forKey: recordsCacheKey(profileId)) {
            records = cached
        }
        // 嘗試從後端更新
        do {
            async let meds = apiClient.fetchMedications(profileId: profileId)
            async let recs = apiClient.fetchMedicationRecords(profileId: profileId)
            (medications, records) = try await (meds, recs)
            // 成功後更新快取
            LocalCache.save(medications, forKey: cacheKey(profileId))
            LocalCache.save(records, forKey: recordsCacheKey(profileId))
        } catch {
            // 失敗時保留快取資料
        }
    }

    func add(medication: Medication, apiClient: APIClientProtocol) async throws {
        let saved = try await apiClient.addMedication(medication)
        medications.append(saved)
    }

    func update(medication: Medication, apiClient: APIClientProtocol) async throws {
        let updated = try await apiClient.updateMedication(medication)
        if let idx = medications.firstIndex(where: { $0.id == updated.id }) {
            medications[idx] = updated
        }
    }

    func delete(id: String, apiClient: APIClientProtocol) async throws {
        try await apiClient.deleteMedication(id: id)
        medications.removeAll { $0.id == id }
        records.removeAll { $0.medicationId == id }
    }

    func recordTaken(medicationId: String, profileId: String, apiClient: APIClientProtocol) async throws {
        let record = MedicationRecord(
            id: UUID().uuidString,
            medicationId: medicationId,
            profileId: profileId,
            scheduledAt: Date(),
            takenAt: Date(),
            status: .taken
        )
        let saved = try await apiClient.recordMedicationTaken(record: record)
        records.append(saved)
        lastTakenRecord = saved
    }

    func recordSkipped(medicationId: String, profileId: String, apiClient: APIClientProtocol) async throws {
        let record = MedicationRecord(
            id: UUID().uuidString,
            medicationId: medicationId,
            profileId: profileId,
            scheduledAt: Date(),
            takenAt: nil,
            status: .skipped
        )
        let saved = try await apiClient.recordMedicationTaken(record: record)
        records.append(saved)
    }

    func undoRecord(recordId: String, apiClient: APIClientProtocol) async throws {
        try await apiClient.deleteAdherenceRecord(id: recordId)
        records.removeAll { $0.id == recordId }
    }

    /// Adherence rate (0.0–1.0) for the past `days` days
    func adherenceRate(medicationId: String, days: Int) -> Double {
        let cutoff = Calendar.current.startOfDay(for: Date().addingTimeInterval(-86400 * Double(days - 1)))
        let relevant = records.filter {
            $0.medicationId == medicationId && $0.scheduledAt >= cutoff
        }
        guard !relevant.isEmpty else { return 0 }
        let taken = relevant.filter { $0.status == .taken }.count
        return Double(taken) / Double(relevant.count)
    }

    /// Records grouped by calendar day for the past `days` days
    func recordsByDay(medicationId: String?, days: Int) -> [(date: Date, taken: Int, total: Int)] {
        let cal = Calendar.current
        return (0..<days).reversed().map { offset in
            let day = cal.startOfDay(for: Date().addingTimeInterval(-86400 * Double(offset)))
            let dayEnd = day.addingTimeInterval(86400)
            let dayRecords = records.filter { r in
                (medicationId == nil || r.medicationId == medicationId) &&
                r.scheduledAt >= day && r.scheduledAt < dayEnd
            }
            return (date: day, taken: dayRecords.filter { $0.status == .taken }.count, total: dayRecords.count)
        }
    }
}
