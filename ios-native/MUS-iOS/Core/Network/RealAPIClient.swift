import Foundation

/// 真實 API 實作（URLSession + Codable）
/// 串接 sprint5 後端：Auth + Medications + Safety + Recognition + Search
final class RealAPIClient: APIClientProtocol {
    let baseURL: URL
    private let session: URLSession
    private let decoder: JSONDecoder
    private let isoFormatter: ISO8601DateFormatter

    init(baseURL: URL = URL(string: "http://localhost:5000")!,
         session: URLSession = .shared) {
        self.baseURL = baseURL
        self.session = session
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder = decoder
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        self.isoFormatter = f
    }

    // MARK: - Bootstrap

    func bootstrap() async {
        // 只驗證已有 token 是否有效，不再自動登入
        if await AuthStore.shared.accessToken() != nil {
            _ = try? await fetchMe()
        }
    }

    private func ensureAuthenticated() async {
        do {
            try await login(username: BackendConstants.testUsername,
                            password: BackendConstants.testPassword)
            return
        } catch APIError.unauthorized, APIError.notFound, APIError.server(_) {
            // try register below
        } catch {
            return
        }
        do {
            try await register(username: BackendConstants.testUsername,
                               password: BackendConstants.testPassword,
                               displayName: BackendConstants.testDisplayName)
            try await login(username: BackendConstants.testUsername,
                            password: BackendConstants.testPassword)
        } catch {
            // fail silently; later calls will surface errors
        }
    }

    private struct LoginResponse: Decodable {
        let accessToken: String
        let refreshToken: String
        let user: UserDTO?
    }
    private struct UserDTO: Decodable {
        let id: Int
        let username: String
        let displayName: String?
    }

    func login(username: String, password: String) async throws {
        let url = baseURL.appendingPathComponent("api/auth/login")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: [
            "username": username, "password": password
        ])
        let (data, resp) = try await session.data(for: req)
        try validate(resp)
        let decoded = try decoder.decode(LoginResponse.self, from: data)
        await AuthStore.shared.setTokens(access: decoded.accessToken, refresh: decoded.refreshToken)
        if let uid = decoded.user?.id { await AuthStore.shared.setUserId(uid) }
        try? await refreshDefaultProfileId()
    }

    func register(username: String, password: String, displayName: String) async throws {
        let url = baseURL.appendingPathComponent("api/auth/register")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: [
            "username": username, "password": password, "display_name": displayName
        ])
        let (_, resp) = try await session.data(for: req)
        try validate(resp)
    }

    private struct MeResponse: Decodable { let success: Bool; let user: UserDTO }
    private func fetchMe() async throws -> UserDTO {
        let data = try await authedGet(path: "api/auth/me")
        return try decoder.decode(MeResponse.self, from: data).user
    }

    private struct ProfilesListResponse: Decodable {
        struct P: Decodable { let id: Int; let name: String?; let isDefault: Bool? }
        let success: Bool
        let profiles: [P]
    }
    private func refreshDefaultProfileId() async throws {
        let data = try await authedGet(path: "api/auth/profiles")
        let decoded = try decoder.decode(ProfilesListResponse.self, from: data)
        let chosen = decoded.profiles.first(where: { $0.isDefault == true })?.id
            ?? decoded.profiles.first?.id
        if let id = chosen { await AuthStore.shared.setProfileId(id) }
    }

    // MARK: - Networking helpers

    private func validate(_ resp: URLResponse) throws {
        guard let http = resp as? HTTPURLResponse else { throw APIError.unknown }
        switch http.statusCode {
        case 200..<300: return
        case 401: throw APIError.unauthorized
        case 403: throw APIError.forbidden
        case 404: throw APIError.notFound
        case 409: throw APIError.conflict
        default: throw APIError.server(http.statusCode)
        }
    }

    private func authed(_ build: () async throws -> URLRequest) async throws -> Data {
        var req = try await build()
        if let token = await AuthStore.shared.accessToken() {
            req.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        let (data, resp) = try await session.data(for: req)
        if let http = resp as? HTTPURLResponse, http.statusCode == 401 {
            await AuthStore.shared.clear()
            await ensureAuthenticated()
            var retry = try await build()
            if let token = await AuthStore.shared.accessToken() {
                retry.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            let (data2, resp2) = try await session.data(for: retry)
            try validate(resp2)
            return data2
        }
        try validate(resp)
        return data
    }

    private func authedGet(path: String, query: [URLQueryItem] = []) async throws -> Data {
        try await authed {
            var comps = URLComponents(url: self.baseURL.appendingPathComponent(path),
                                      resolvingAgainstBaseURL: false)!
            if !query.isEmpty { comps.queryItems = query }
            var req = URLRequest(url: comps.url!)
            req.httpMethod = "GET"
            return req
        }
    }

    private func authedJSON(method: String, path: String, body: Any? = nil) async throws -> Data {
        try await authed {
            var req = URLRequest(url: self.baseURL.appendingPathComponent(path))
            req.httpMethod = method
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            if let body {
                req.httpBody = try JSONSerialization.data(withJSONObject: body)
            }
            return req
        }
    }

    // MARK: - Recognition / Search / Drug (public)

    private struct DrugDTO: Decodable {
        let id: Int
        let chineseName: String?
        let englishName: String?
        let licenseNumber: String?
        let shape: String?
        let color: String?
        let usage: String?
        let indications: String?
        let images: [DrugImageDTO]?
    }
    private struct DrugImageDTO: Decodable {
        let path: String?
        let filename: String?
    }
    private struct SearchResponse: Decodable { let success: Bool; let results: [DrugDTO] }
    private struct DrugResponse: Decodable { let success: Bool; let drug: DrugDTO }

    private func makeDrug(_ dto: DrugDTO) -> Drug {
        let img = dto.images?.first.flatMap { d -> URL? in
            guard let raw = d.path ?? d.filename, !raw.isEmpty else { return nil }
            let normalized = raw.replacingOccurrences(of: "\\", with: "/")
            let encoded = normalized.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? normalized
            return URL(string: "api/images/\(encoded)", relativeTo: baseURL)?.absoluteURL
        }
        return Drug(id: dto.id,
                    chineseName: dto.chineseName ?? "",
                    englishName: dto.englishName,
                    licenseNumber: dto.licenseNumber,
                    shape: dto.shape,
                    color: dto.color,
                    usage: dto.usage ?? dto.indications,
                    imageURL: img)
    }

    private struct RecognizeResponse: Decodable {
        let success: Bool
        let requestId: String
        let recognizedItems: [RecognizedItemPayload]
    }
    private struct RecognizedItemPayload: Decodable {
        let name: String; let confidence: Double; let drugId: Int?
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
        let items = decoded.recognizedItems.map {
            RecognitionItem(drugId: $0.drugId ?? 0, name: $0.name, confidence: $0.confidence)
        }
        return RecognitionResult(requestId: decoded.requestId, items: items)
    }

    
    private struct PrescriptionResponse: Decodable {
        let success: Bool
        let requestId: String?
        let recognizedDrugs: [String]?
        let recognizedItems: [PrescriptionItemPayload]?
        let message: String?
        let error: String?

    }
    private struct PrescriptionItemPayload: Decodable {
        let name: String
        let confidence: Double
        let source: String?
        let drugId: Int?
        let prescriptionInfo: PrescriptionInfo?
        let details: PrescriptionDrugInfo?
    }

    func recognizePrescription(imageData: Data) async throws -> PrescriptionOCRResult {
        let url = baseURL.appendingPathComponent("api/recognize_prescription")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        let boundary = "Boundary-\(UUID().uuidString)"
        req.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        var body = Data()
        body.append("--\(boundary)\r\n".data(using: .utf8)!)
        body.append("Content-Disposition: form-data; name=\"image\"; filename=\"prescription.jpg\"\r\n".data(using: .utf8)!)
        body.append("Content-Type: image/jpeg\r\n\r\n".data(using: .utf8)!)
        body.append(imageData)
        body.append("\r\n--\(boundary)--\r\n".data(using: .utf8)!)
        req.httpBody = body
        let (data, resp) = try await session.data(for: req)
        try validate(resp)
        if let raw = String(data: data, encoding: .utf8) {
            print("[OCR DEBUG] raw response: \(raw.prefix(2000))")
        }
        let decoded = try decoder.decode(PrescriptionResponse.self, from: data)
        guard decoded.success else {
            throw APIError.network(NSError(domain: "", code: 0, userInfo: [NSLocalizedDescriptionKey: decoded.error ?? decoded.message ?? "OCR 辨識失敗"]))
        }
        let details = (decoded.recognizedItems ?? []).map {
            print("[OCR DEBUG] item: \($0.name), prescriptionInfo: \(String(describing: $0.prescriptionInfo)), details: \(String(describing: $0.details))")
            return PrescriptionDrugDetail(
                name: $0.name,
                confidence: $0.confidence,
                source: $0.source ?? "prescription",
                drugId: $0.drugId,
                prescriptionInfo: $0.prescriptionInfo,
                details: $0.details
            )
        }
        return PrescriptionOCRResult(
            requestId: decoded.requestId ?? UUID().uuidString,
            recognizedDrugs: decoded.recognizedDrugs ?? [],
            drugDetails: details,
            message: decoded.message ?? ""
        )
    }

    func fetchDrug(id: Int) async throws -> Drug {
        let url = baseURL.appendingPathComponent("api/drug/\(id)")
        let (data, resp) = try await session.data(from: url)
        try validate(resp)
        return makeDrug(try decoder.decode(DrugResponse.self, from: data).drug)
    }

    func searchDrugs(query: String, limit: Int) async throws -> [Drug] {
        let url = baseURL.appendingPathComponent("api/search")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(withJSONObject: ["query": query, "limit": limit])
        let (data, resp) = try await session.data(for: req)
        try validate(resp)
        return try decoder.decode(SearchResponse.self, from: data).results.map(makeDrug)
    }

    // MARK: - Profiles

    func fetchProfiles() async throws -> [Profile] {
        let data = try await authedGet(path: "api/auth/profiles")
        let decoded = try decoder.decode(ProfilesListResponse.self, from: data)
        return decoded.profiles.map { p in
            Profile(id: String(p.id),
                    name: (p.name?.isEmpty == false ? p.name! : "本人"),
                    isPrimary: p.isDefault ?? false,
                    avatarSystemName: "person.crop.circle")
        }
    }

    // MARK: - Medications

    private struct MedicationDTO: Decodable {
        let id: Int
        let userId: Int
        let profileId: Int
        let drugId: Int?
        let name: String
        let dosage: String?
        let unit: String?
        let frequency: String?
        let durationDays: Int?
        let startDate: String?
        let endDate: String?
        let stockQty: Int?
        let note: String?
        let isActive: Bool?
        let schedules: [ScheduleDTO]?
    }
    private struct ScheduleDTO: Decodable {
        let id: Int?
        let medicationId: Int?
        let timeSlot: String?
        let scheduledTime: String?
        let doseQty: Double?
    }
    private struct MedicationsResponse: Decodable {
        let success: Bool; let medications: [MedicationDTO]
    }
    private struct MedicationResponse: Decodable {
        let success: Bool; let medication: MedicationDTO
    }

    func fetchMedications(profileId: String) async throws -> [Medication] {
        let pid = await resolvedProfileId(from: profileId)
        let data = try await authedGet(
            path: "api/user/medications",
            query: [URLQueryItem(name: "profile_id", value: String(pid)),
                    URLQueryItem(name: "active", value: "true")]
        )
        return try decoder.decode(MedicationsResponse.self, from: data)
            .medications.map { mapMedication($0) }
    }

    func addMedication(_ medication: Medication) async throws -> Medication {
        let pid = await resolvedProfileId(from: medication.profileId)
        let body = buildMedicationBody(medication: medication, profileId: pid)
        let data = try await authedJSON(method: "POST", path: "api/user/medications", body: body)
        return mapMedication(try decoder.decode(MedicationResponse.self, from: data).medication)
    }

    func updateMedication(_ medication: Medication) async throws -> Medication {
        guard let medId = Int(medication.id) else { throw APIError.invalidURL }
        let pid = await resolvedProfileId(from: medication.profileId)
        let body = buildMedicationBody(medication: medication, profileId: pid)
        let data = try await authedJSON(method: "PUT",
                                        path: "api/user/medications/\(medId)",
                                        body: body)
        return mapMedication(try decoder.decode(MedicationResponse.self, from: data).medication)
    }

    func deleteMedication(id: String) async throws {
        guard let medId = Int(id) else { throw APIError.invalidURL }
        _ = try await authedJSON(method: "DELETE", path: "api/user/medications/\(medId)")
    }

    private func buildMedicationBody(medication m: Medication, profileId: Int) -> [String: Any] {
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm"
        timeFormatter.timeZone = TimeZone(identifier: "Asia/Taipei")
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone(identifier: "Asia/Taipei")

        let slots = ["morning", "noon", "evening", "night"]
        let schedules: [[String: Any]] = m.reminderTimes.enumerated().map { (idx, date) in
            return [
                "time_slot": slots[min(idx, slots.count - 1)],
                "scheduled_time": timeFormatter.string(from: date),
                "dose_qty": 1.0
            ]
        }

        var body: [String: Any] = [
            "profile_id": profileId,
            "name": m.drugName,
            "dosage": m.dosage,
            "frequency": mapFrequency(m.frequency),
            "start_date": dateFormatter.string(from: m.nextDoseAt),
            "stock_qty": m.currentStock,
            "note": buildNote(medication: m),
        ]
        if !schedules.isEmpty { body["schedules"] = schedules }
        return body
    }

    private func buildNote(medication m: Medication) -> String {
        var noteContent = ""
        if let label = m.prescriptionLabel, !label.isEmpty {
            noteContent = "[RX:\(label)]"
            if !m.notes.isEmpty { noteContent += " \(m.notes)" }
        } else {
            noteContent = m.notes
        }
        if noteContent.isEmpty {
            return m.mealTiming
        }
        return "\(m.mealTiming)\n\(noteContent)"
    }

    private func mapMedication(_ dto: MedicationDTO) -> Medication {
        let timeFormatter = DateFormatter()
        timeFormatter.dateFormat = "HH:mm"
        timeFormatter.timeZone = TimeZone(identifier: "Asia/Taipei")
        let cal = Calendar(identifier: .gregorian)
        let today = Date()
        let reminders: [Date] = (dto.schedules ?? []).compactMap { s in
            guard let hhmm = s.scheduledTime,
                  let timeOnly = timeFormatter.date(from: hhmm) else { return nil }
            let comps = cal.dateComponents([.hour, .minute], from: timeOnly)
            return cal.date(bySettingHour: comps.hour ?? 0,
                            minute: comps.minute ?? 0, second: 0, of: today)
        }
        let next = reminders.first(where: { $0 > today }) ?? reminders.first ?? today

        let noteParts = (dto.note ?? "").split(separator: "\n", maxSplits: 1).map(String.init)
        let mealTiming = noteParts.first ?? ""
        let rawNotes = noteParts.count > 1 ? noteParts[1] : ""

        // Parse prescriptionLabel from notes (format: "[RX:label]rest of notes")
        var prescriptionLabel: String? = nil
        var notes = rawNotes
        if rawNotes.hasPrefix("[RX:") {
            if let end = rawNotes.range(of: "]") {
                prescriptionLabel = String(rawNotes[rawNotes.index(rawNotes.startIndex, offsetBy: 4)..<end.lowerBound])
                notes = String(rawNotes[end.upperBound...]).trimmingCharacters(in: .whitespaces)
            }
        }

        return Medication(
            id: String(dto.id),
            profileId: String(dto.profileId),
            drugName: dto.name,
            dosage: dto.dosage ?? "",
            frequency: humanFrequency(dto.frequency ?? "daily"),
            mealTiming: mealTiming,
            nextDoseAt: next,
            currentStock: dto.stockQty ?? 0,
            reminderTimes: reminders,
            notes: notes,
            prescriptionLabel: prescriptionLabel
        )
    }

    private func mapFrequency(_ freq: String) -> String {
        let s = freq.lowercased()
        if s.contains("4") || s.contains("四") || s.contains("qid") { return "qid" }
        if s.contains("3") || s.contains("三") || s.contains("tid") { return "tid" }
        if s.contains("2") || s.contains("二") || s.contains("早晚") || s.contains("bid") { return "bid" }
        if s.contains("需要") || s.contains("prn") { return "prn" }
        return "daily"
    }
    private func humanFrequency(_ enumVal: String) -> String {
        switch enumVal.lowercased() {
        case "qid": return "每日 4 次"
        case "tid": return "每日 3 次"
        case "bid": return "每日 2 次"
        case "prn": return "需要時服用"
        default: return "每日 1 次"
        }
    }

    // MARK: - Adherence

    private struct AdherenceLogDTO: Decodable {
        let id: Int
        let userId: Int
        let medicationId: Int
        let scheduleId: Int?
        let status: String
        let takenAt: String?
        let scheduledDate: String?
        let note: String?
    }
    private struct AdherenceListResponse: Decodable {
        let success: Bool; let logs: [AdherenceLogDTO]
    }
    private struct AdherenceLogResponse: Decodable {
        let success: Bool; let log: AdherenceLogDTO
    }

    func fetchMedicationRecords(profileId: String) async throws -> [MedicationRecord] {
        let data = try await authedGet(path: "api/user/adherence")
        return try decoder.decode(AdherenceListResponse.self, from: data)
            .logs.map { mapAdherence($0) }
    }

    func recordMedicationTaken(record: MedicationRecord) async throws -> MedicationRecord {
        guard let medId = Int(record.medicationId) else { throw APIError.invalidURL }
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone(identifier: "Asia/Taipei")
        let body: [String: Any] = [
            "medication_id": medId,
            "status": mapRecordStatus(record.status),
            "scheduled_date": dateFormatter.string(from: record.scheduledAt),
        ]
        let data = try await authedJSON(method: "POST", path: "api/user/adherence", body: body)
        return mapAdherence(try decoder.decode(AdherenceLogResponse.self, from: data).log)
    }

    private func mapAdherence(_ dto: AdherenceLogDTO) -> MedicationRecord {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        dateFormatter.timeZone = TimeZone(identifier: "Asia/Taipei")
        let scheduled = dto.scheduledDate.flatMap { dateFormatter.date(from: $0) } ?? Date()
        let taken = dto.takenAt.flatMap { isoFormatter.date(from: $0) }
        let status: MedicationRecord.Status
        switch dto.status {
        case "taken", "late": status = .taken
        case "skipped": status = .skipped
        default: status = .snoozed
        }
        return MedicationRecord(
            id: String(dto.id),
            medicationId: String(dto.medicationId),
            profileId: "",
            scheduledAt: scheduled,
            takenAt: taken,
            status: status
        )
    }

    private func mapRecordStatus(_ s: MedicationRecord.Status) -> String {
        switch s {
        case .taken: return "taken"
        case .skipped, .snoozed: return "skipped"
        }
    }

    // MARK: - Safety

    private struct SafetyCheckResponse: Decodable {
        let success: Bool
        let overall: String
        let checks: [SafetyCheckItem]
    }
    private struct SafetyCheckItem: Decodable {
        let type: String
        let result: String
        let detail: String?
        let allergens: [String]?
        let duplicates: [String]?
    }

    func checkSafety(profileId: String, drugIds: [Int]) async throws -> [SafetyAlert] {
        let pid = await resolvedProfileId(from: profileId)
        var alerts: [SafetyAlert] = []
        for drugId in drugIds {
            let body: [String: Any] = ["drug_id": drugId, "profile_id": pid]
            do {
                let data = try await authedJSON(method: "POST", path: "api/safety/check", body: body)
                let decoded = try decoder.decode(SafetyCheckResponse.self, from: data)
                for c in decoded.checks where c.result != "safe" {
                    let level: SafetyAlert.Level = {
                        switch c.result {
                        case "danger": return .major
                        case "warning": return .moderate
                        default: return .minor
                        }
                    }()
                    let title: String = {
                        switch c.type {
                        case "allergy": return "過敏風險"
                        case "duplicate": return "重複用藥"
                        case "interaction": return "交互作用"
                        default: return c.type
                        }
                    }()
                    alerts.append(SafetyAlert(
                        id: "\(drugId)-\(c.type)",
                        level: level,
                        title: title,
                        message: c.detail ?? "",
                        recommendation: ""
                    ))
                }
            } catch {
                continue
            }
        }
        return alerts
    }

    private struct AllergyDTO: Decodable {
        let id: Int
        let userId: Int?
        let ingredientId: Int
        let ingredientName: String?
        let severity: String?
        let note: String?
    }
    private struct AllergiesListResponse: Decodable {
        let success: Bool; let allergies: [AllergyDTO]
    }
    private struct AllergyResponse: Decodable {
        let success: Bool; let allergy: AllergyDTO
    }

    func fetchAllergyItems(profileId: String) async throws -> [AllergyItem] {
        let data = try await authedGet(path: "api/safety/allergies")
        return try decoder.decode(AllergiesListResponse.self, from: data).allergies.map { dto in
            AllergyItem(
                id: String(dto.id),
                profileId: profileId,
                name: dto.ingredientName ?? "成分#\(dto.ingredientId)"
            )
        }
    }

    func addAllergyItem(_ item: AllergyItem) async throws -> AllergyItem {
        // 後端需要 ingredient_id (FK)，iOS 只有 name；暫以「輸入數字 ID」模式 fallback
        guard let ingredientId = Int(item.name) else {
            throw APIError.server(400)
        }
        let body: [String: Any] = ["ingredient_id": ingredientId, "severity": "moderate"]
        let data = try await authedJSON(method: "POST", path: "api/safety/allergies", body: body)
        let decoded = try decoder.decode(AllergyResponse.self, from: data)
        return AllergyItem(
            id: String(decoded.allergy.id),
            profileId: item.profileId,
            name: decoded.allergy.ingredientName ?? item.name
        )
    }

    func deleteAllergyItem(id: String) async throws {
        guard let aid = Int(id) else { throw APIError.invalidURL }
        _ = try await authedJSON(method: "DELETE", path: "api/safety/allergies/\(aid)")
    }

    // MARK: - Not implemented

    func fetchConsultations() async throws -> [ConsultationSummary] { throw APIError.unknown }
    func fetchNearbyPharmacies(latitude: Double, longitude: Double, radius: Double) async throws -> [Pharmacy] { throw APIError.unknown }

    // MARK: - AI Consultation

    private struct AIResponse: Decodable {
        let success: Bool
        let reply: String?
        let error: String?
    }

    func askAI(question: String) async throws -> String {
        let data = try await authedJSON(method: "POST", path: "api/consultation/ask", body: [
            "question": question
        ])
        let decoded = try decoder.decode(AIResponse.self, from: data)
        if let reply = decoded.reply { return reply }
        throw APIError.server(500)
    }

    // MARK: - Helpers

    private func resolvedProfileId(from iosId: String) async -> Int {
        if let id = Int(iosId), id > 0 { return id }
        if let stored = await AuthStore.shared.profileId() { return stored }
        return 1
    }
}
