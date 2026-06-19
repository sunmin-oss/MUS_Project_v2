import UserNotifications
import Foundation

@MainActor
final class NotificationManager: ObservableObject {
    static let shared = NotificationManager()

    @Published var authorizationStatus: UNAuthorizationStatus = .notDetermined

    static let medicationReminderCategoryId = "medication.reminder"
    static let actionTaken = "medication.taken"
    static let actionSnooze = "medication.snooze"
    static let actionSkip = "medication.skip"

    private init() {
        registerCategories()
        Task { await checkAuthorizationStatus() }
    }

    func requestPermission() async -> Bool {
        do {
            let granted = try await UNUserNotificationCenter.current()
                .requestAuthorization(options: [.alert, .sound, .badge])
            await checkAuthorizationStatus()
            return granted
        } catch {
            return false
        }
    }

    func checkAuthorizationStatus() async {
        let settings = await UNUserNotificationCenter.current().notificationSettings()
        authorizationStatus = settings.authorizationStatus
    }

    func registerCategories() {
        let takenAction = UNNotificationAction(
            identifier: Self.actionTaken,
            title: "✅ 已服藥",
            options: .foreground
        )
        let snoozeAction = UNNotificationAction(
            identifier: Self.actionSnooze,
            title: "⏰ 延後 15 分鐘",
            options: []
        )
        let skipAction = UNNotificationAction(
            identifier: Self.actionSkip,
            title: "❌ 略過這次",
            options: .destructive
        )
        let category = UNNotificationCategory(
            identifier: Self.medicationReminderCategoryId,
            actions: [takenAction, snoozeAction, skipAction],
            intentIdentifiers: []
        )
        UNUserNotificationCenter.current().setNotificationCategories([category])
    }

    func scheduleMedicationReminder(medication: Medication, at time: Date) async {
        let content = UNMutableNotificationContent()
        content.title = "用藥提醒"
        content.body = "\(medication.drugName)・\(medication.dosage)"
        content.sound = .default
        content.categoryIdentifier = Self.medicationReminderCategoryId
        content.userInfo = ["medicationId": medication.id]

        let components = Calendar.current.dateComponents([.hour, .minute], from: time)
        let trigger = UNCalendarNotificationTrigger(dateMatching: components, repeats: true)
        let identifier = "med.\(medication.id).\(components.hour ?? 0).\(components.minute ?? 0)"
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        try? await UNUserNotificationCenter.current().add(request)
    }

    func cancelReminders(for medicationId: String) async {
        let pending = await UNUserNotificationCenter.current().pendingNotificationRequests()
        let ids = pending.filter { $0.identifier.hasPrefix("med.\(medicationId).") }.map { $0.identifier }
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: ids)
    }

    func scheduleStockAlert(medication: Medication) async {
        guard medication.currentStock <= 7 else { return }
        let content = UNMutableNotificationContent()
        content.title = "庫存不足提醒"
        content.body = "\(medication.drugName) 剩餘 \(medication.currentStock.stockDisplay) 顆，請盡快補充"
        content.sound = .default

        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 5, repeats: false)
        let identifier = "stock.\(medication.id)"
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)
        try? await UNUserNotificationCenter.current().add(request)
    }

    func listPending() async -> [UNNotificationRequest] {
        await UNUserNotificationCenter.current().pendingNotificationRequests()
    }
}
