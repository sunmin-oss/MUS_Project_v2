import Foundation

@MainActor
final class MedicationStore: ObservableObject {
    @Published var medications: [Medication] = []
    @Published var records: [MedicationRecord] = []

    func load(profileId: String, apiClient: APIClientProtocol) async {
        do {
            async let meds = apiClient.fetchMedications(profileId: profileId)
            async let recs = apiClient.fetchMedicationRecords(profileId: profileId)
            (medications, records) = try await (meds, recs)
        } catch {
            // keep existing state on error
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

    func recordTaken(medicationId: String, profileId: String) async {
        let record = MedicationRecord(
            id: UUID().uuidString,
            medicationId: medicationId,
            profileId: profileId,
            scheduledAt: Date(),
            takenAt: Date(),
            status: .taken
        )
        records.append(record)
    }

    func recordSkipped(medicationId: String, profileId: String) async {
        let record = MedicationRecord(
            id: UUID().uuidString,
            medicationId: medicationId,
            profileId: profileId,
            scheduledAt: Date(),
            takenAt: nil,
            status: .skipped
        )
        records.append(record)
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
