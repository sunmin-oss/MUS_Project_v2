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
}

struct Profile: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let isPrimary: Bool
    let avatarSystemName: String
}

struct Medication: Identifiable, Codable, Hashable {
    let id: String
    let profileId: String
    let drugName: String
    let dosage: String
    let frequency: String
    let mealTiming: String
    let nextDoseAt: Date
    let currentStock: Int
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
