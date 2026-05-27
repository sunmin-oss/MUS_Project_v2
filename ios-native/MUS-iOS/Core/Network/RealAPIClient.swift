import Foundation

/// 真實 API 實作（URLSession + Codable）
/// W1 階段僅留骨架；Phase 3 接後端時逐一補上各端點
final class RealAPIClient: APIClientProtocol {
    let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder

    init(baseURL: URL = URL(string: "http://localhost:5000")!,
         session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder = decoder
    }

    // 以下方法 Phase 3 實作；目前回傳未實作錯誤
    func recognizeDrug(imageData: Data) async throws -> RecognitionResult { throw APIError.unknown }
    func fetchDrug(id: Int) async throws -> Drug { throw APIError.unknown }
    func searchDrugs(query: String, limit: Int) async throws -> [Drug] { throw APIError.unknown }
    func fetchProfiles() async throws -> [Profile] { throw APIError.unknown }
    func fetchMedications(profileId: String) async throws -> [Medication] { throw APIError.unknown }
    func fetchConsultations() async throws -> [ConsultationSummary] { throw APIError.unknown }
    func fetchNearbyPharmacies(latitude: Double, longitude: Double, radius: Double) async throws -> [Pharmacy] { throw APIError.unknown }
    func checkSafety(profileId: String, drugIds: [Int]) async throws -> [SafetyAlert] { throw APIError.unknown }

    // MARK: - W3 stubs
    func fetchMedicationRecords(profileId: String) async throws -> [MedicationRecord] { throw APIError.unknown }
    func addMedication(_ medication: Medication) async throws -> Medication { throw APIError.unknown }
    func updateMedication(_ medication: Medication) async throws -> Medication { throw APIError.unknown }
    func deleteMedication(id: String) async throws { throw APIError.unknown }
    func recordMedicationTaken(record: MedicationRecord) async throws -> MedicationRecord { throw APIError.unknown }
    func fetchAllergyItems(profileId: String) async throws -> [AllergyItem] { throw APIError.unknown }
    func addAllergyItem(_ item: AllergyItem) async throws -> AllergyItem { throw APIError.unknown }
    func deleteAllergyItem(id: String) async throws { throw APIError.unknown }
}
