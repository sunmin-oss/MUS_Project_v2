import Foundation

/// API 錯誤型別
enum APIError: LocalizedError {
    case invalidURL
    case unauthorized
    case forbidden
    case notFound
    case conflict
    case server(Int)
    case decoding(Error)
    case network(Error)
    case unknown

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "無效的 URL"
        case .unauthorized: return "請重新登入"
        case .forbidden: return "權限不足"
        case .notFound: return "資源不存在"
        case .conflict: return "資源已存在"
        case .server(let code): return "伺服器錯誤（\(code)）"
        case .decoding: return "資料格式錯誤"
        case .network(let err): return "網路錯誤：\(err.localizedDescription)"
        case .unknown: return "未知錯誤"
        }
    }
}

/// APIClient 抽象介面。MockAPIClient 與 RealAPIClient 雙實作，可由 AppEnvironment 切換注入。
/// Phase 3 接後端時：替換 AppEnvironment.makeDefault() 內的實作即可，View 層無需修改。
protocol APIClientProtocol {
    /// 啟動時呼叫；RealAPIClient 用來自動 register-or-login，Mock 可空實作
    func bootstrap() async

    // MARK: - Recognition
    func recognizeDrug(imageData: Data) async throws -> RecognitionResult
    func recognizePrescription(imageData: Data) async throws -> PrescriptionOCRResult
    func fetchDrug(id: Int) async throws -> Drug
    func searchDrugs(query: String, limit: Int) async throws -> [Drug]

    // MARK: - Profile
    func fetchProfiles() async throws -> [Profile]

    // MARK: - Medications (Spec 01)
    func fetchMedications(profileId: String) async throws -> [Medication]

    // MARK: - Consultations (Spec 02)
    func fetchConsultations() async throws -> [ConsultationSummary]

    // MARK: - Pharmacies (Spec 03)
    func fetchNearbyPharmacies(latitude: Double, longitude: Double, radius: Double) async throws -> [Pharmacy]

    // MARK: - Safety (Spec 06)
    func checkSafety(profileId: String, drugIds: [Int]) async throws -> [SafetyAlert]

    // MARK: - W3: Medication Records & CRUD
    func fetchMedicationRecords(profileId: String) async throws -> [MedicationRecord]
    func addMedication(_ medication: Medication) async throws -> Medication
    func updateMedication(_ medication: Medication) async throws -> Medication
    func deleteMedication(id: String) async throws
    func recordMedicationTaken(record: MedicationRecord) async throws -> MedicationRecord

    // MARK: - W3: Allergy
    func fetchAllergyItems(profileId: String) async throws -> [AllergyItem]
    func addAllergyItem(_ item: AllergyItem) async throws -> AllergyItem
    func deleteAllergyItem(id: String) async throws
}
