import Foundation

/// Mock API Client：W1 與 Demo 模式使用
/// 模擬真實 API 的延遲，方便 ProgressView 測試
final class MockAPIClient: APIClientProtocol {
    private let simulatedLatency: Duration

    init(latencyMillis: Int = 400) {
        self.simulatedLatency = .milliseconds(latencyMillis)
    }

    private func delay() async {
        try? await Task.sleep(for: simulatedLatency)
    }

    func recognizeDrug(imageData: Data) async throws -> RecognitionResult {
        await delay()
        let items = MockData.drugs.prefix(2).map {
            RecognitionItem(drugId: $0.id, name: $0.chineseName, confidence: 0.88)
        }
        return RecognitionResult(requestId: UUID().uuidString, items: Array(items))
    }

    func fetchDrug(id: Int) async throws -> Drug {
        await delay()
        guard let drug = MockData.drugs.first(where: { $0.id == id }) else { throw APIError.notFound }
        return drug
    }

    func searchDrugs(query: String, limit: Int) async throws -> [Drug] {
        await delay()
        let filtered = MockData.drugs.filter {
            $0.chineseName.contains(query) || ($0.englishName?.localizedCaseInsensitiveContains(query) ?? false)
        }
        return Array((filtered.isEmpty ? MockData.drugs : filtered).prefix(limit))
    }

    func fetchProfiles() async throws -> [Profile] {
        await delay()
        return MockData.profiles
    }

    func fetchMedications(profileId: String) async throws -> [Medication] {
        await delay()
        return MockData.medications.filter { $0.profileId == profileId }
    }

    func fetchConsultations() async throws -> [ConsultationSummary] {
        await delay()
        return MockData.consultations
    }

    func fetchNearbyPharmacies(latitude: Double, longitude: Double, radius: Double) async throws -> [Pharmacy] {
        await delay()
        return MockData.pharmacies
    }

    func checkSafety(profileId: String, drugIds: [Int]) async throws -> [SafetyAlert] {
        await delay()
        return MockData.safetyAlerts
    }

    // MARK: - W3
    func fetchMedicationRecords(profileId: String) async throws -> [MedicationRecord] {
        await delay()
        return MockData.medicationRecords.filter { $0.profileId == profileId }
    }

    func addMedication(_ medication: Medication) async throws -> Medication {
        await delay()
        var m = medication
        m.id = UUID().uuidString
        return m
    }

    func updateMedication(_ medication: Medication) async throws -> Medication {
        await delay()
        return medication
    }

    func deleteMedication(id: String) async throws {
        await delay()
    }

    func recordMedicationTaken(record: MedicationRecord) async throws -> MedicationRecord {
        await delay()
        return record
    }

    func fetchAllergyItems(profileId: String) async throws -> [AllergyItem] {
        await delay()
        return MockData.allergyItems.filter { $0.profileId == profileId }
    }

    func addAllergyItem(_ item: AllergyItem) async throws -> AllergyItem {
        await delay()
        return item
    }

    func deleteAllergyItem(id: String) async throws {
        await delay()
    }
}
