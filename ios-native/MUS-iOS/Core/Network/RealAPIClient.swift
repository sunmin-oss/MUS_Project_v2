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

    // MARK: - 真實後端串接（80d4edf 測試用，僅 search / fetchDrug / recognize）
    private struct SearchResponse: Decodable {
        let success: Bool
        let results: [Drug]
    }
    private struct DrugResponse: Decodable {
        let success: Bool
        let drug: Drug
    }
    private struct RecognizeResponse: Decodable {
        let success: Bool
        let requestId: String
        let recognizedItems: [RecognizedItemPayload]
    }
    private struct RecognizedItemPayload: Decodable {
        let name: String
        let confidence: Double
        let drugId: Int?
    }

    private func validate(_ resp: URLResponse) throws {
        guard let http = resp as? HTTPURLResponse else { throw APIError.unknown }
        switch http.statusCode {
        case 200..<300: return
        case 401: throw APIError.unauthorized
        case 403: throw APIError.forbidden
        case 404: throw APIError.notFound
        default: throw APIError.server(http.statusCode)
        }
    }

    func recognizeDrug(imageData: Data) async throws -> RecognitionResult {
        let url = baseURL.appendingPathComponent("api/recognize")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"upload.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        req.httpBody = body
        let (data, resp) = try await session.data(for: req)
        try validate(resp)
        let decoded = try decoder.decode(RecognizeResponse.self, from: data)
        let items = decoded.recognizedItems.map { p in
            RecognitionItem(drugId: p.drugId ?? 0, name: p.name, confidence: p.confidence)
        }
        return RecognitionResult(requestId: decoded.requestId, items: items)
    }

    func fetchDrug(id: Int) async throws -> Drug {
        let url = baseURL.appendingPathComponent("api/drug/\(id)")
        let (data, resp) = try await session.data(from: url)
        try validate(resp)
        let decoded = try decoder.decode(DrugResponse.self, from: data)
        return decoded.drug
    }

    func searchDrugs(query: String, limit: Int) async throws -> [Drug] {
        let url = baseURL.appendingPathComponent("api/search")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body: [String: Any] = ["query": query, "limit": limit]
        req.httpBody = try JSONSerialization.data(withJSONObject: body)
        let (data, resp) = try await session.data(for: req)
        try validate(resp)
        let decoded = try decoder.decode(SearchResponse.self, from: data)
        return decoded.results
    }

    // MARK: - 其餘端點 (此 commit 後端未實作)
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
