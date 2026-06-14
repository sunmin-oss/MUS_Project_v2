import Foundation

/// 共用模型（DTO）。對應 Backend Roadmap 的資料表結構
/// W1 階段先定義最小欄位，Phase 3 串接 API 時可擴充

struct Drug: Identifiable, Codable, Hashable {
    let id: Int
    let chineseName: String
    let englishName: String?
    let licenseNumber: String?
    let shape: String?
    let color: String?
    let usage: String?
    let imageURL: URL?
}

struct Profile: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let isPrimary: Bool
    let avatarSystemName: String
}

struct Medication: Identifiable, Codable, Hashable {
    var id: String
    var profileId: String
    var drugName: String
    var dosage: String
    var frequency: String
    var mealTiming: String
    var nextDoseAt: Date
    var currentStock: Int
    var reminderTimes: [Date]
    var notes: String
}

struct ConsultationSummary: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let lastMessagePreview: String
    let updatedAt: Date
    let isAI: Bool
}

struct Pharmacy: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let address: String
    let latitude: Double
    let longitude: Double
    let isNHIContracted: Bool
    let is24h: Bool
}

struct SafetyAlert: Identifiable, Codable, Hashable {
    enum Level: String, Codable { case contraindicated, major, moderate, minor }
    let id: String
    let level: Level
    let title: String
    let message: String
    let recommendation: String
}

// MARK: - W3 Models

struct MedicationRecord: Identifiable, Codable, Hashable {
    enum Status: String, Codable { case taken, skipped, snoozed }
    let id: String
    let medicationId: String
    let profileId: String
    let scheduledAt: Date
    var takenAt: Date?
    var status: Status
}

struct AllergyItem: Identifiable, Codable, Hashable {
    let id: String
    let profileId: String
    let name: String
}

struct RecognitionResult: Codable, Hashable {
    let requestId: String
    let items: [RecognitionItem]
}

struct RecognitionItem: Identifiable, Codable, Hashable {
    var id: Int { drugId }
    let drugId: Int
    let name: String
    let confidence: Double
}
