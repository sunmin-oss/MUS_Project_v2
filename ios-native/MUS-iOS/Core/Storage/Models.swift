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
    var currentStock: Double
    var reminderTimes: [Date]
    var notes: String
    var prescriptionLabel: String?
}

extension Double {
    /// 庫存顯示：整數顯示無小數 (12)，非整數保留一位 (4.5)
    var stockDisplay: String {
        truncatingRemainder(dividingBy: 1) == 0 ? String(format: "%.0f", self) : String(format: "%.1f", self)
    }
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

struct PrescriptionOCRResult: Codable {
    let requestId: String
    let recognizedDrugs: [String]
    let drugDetails: [PrescriptionDrugDetail]
    let message: String
}

struct PrescriptionDrugDetail: Identifiable, Codable {
    var id: String { name }
    let name: String
    let confidence: Double
    let source: String
    let drugId: Int?
    let prescriptionInfo: PrescriptionInfo?
    let details: PrescriptionDrugInfo?
}

struct PrescriptionInfo: Codable {
    let route: String?
    let days: Int?
    let frequency: String?
    let dosePerTime: String?
    let totalQuantity: String?
    let ingredient: String?
}

struct PrescriptionDrugInfo: Codable {
    let chineseName: String?
    let englishName: String?
    let licenseNumber: String?
    let shape: String?
    let color: String?
    let indications: String?
}

