import Foundation
import SwiftUI

/// 全域依賴容器（DI）。所有跨模組服務從此注入。
@MainActor
final class AppEnvironment: ObservableObject {
    @Published var apiClient: APIClientProtocol

    /// 共享的藥物 Store（跨頁面同步用，避免重複實例）
    let medicationStore: MedicationStore

    /// 使用者是否已登入
    @Published var isAuthenticated: Bool = false

    /// 目前登入的使用者名稱
    @Published var currentUsername: String?

    /// Demo 模式：使用 Mock 資料；發佈前可由「我的」分頁切換
    @Published var isDemoMode: Bool {
        didSet {
            UserDefaults.standard.set(isDemoMode, forKey: "isDemoMode")
            apiClient = Self.makeClient(isDemoMode: isDemoMode)
            if isDemoMode {
                isAuthenticated = true
            }
        }
    }

    /// 目前選取的成員 profileId（跨頁面同步）
    @Published var selectedProfileId: String {
        didSet { UserDefaults.standard.set(selectedProfileId, forKey: "selectedProfileId") }
    }

    init(isDemoMode: Bool) {
        self.isDemoMode = isDemoMode
        self.apiClient = Self.makeClient(isDemoMode: isDemoMode)
        self.selectedProfileId = UserDefaults.standard.string(forKey: "selectedProfileId") ?? "p1"
        self.medicationStore = MedicationStore()

        if isDemoMode {
            isAuthenticated = true
        } else {
            // 檢查是否有已保存的 token（恢復登入狀態）
            Task {
                if let token = await AuthStore.shared.accessToken(), !token.isEmpty {
                    self.isAuthenticated = true
                    self.currentUsername = UserDefaults.standard.string(forKey: "currentUsername")
                    if let pid = await AuthStore.shared.profileId(), pid > 0 {
                        self.selectedProfileId = String(pid)
                        await self.medicationStore.load(profileId: String(pid), apiClient: self.apiClient)
                    }
                }
            }
        }
    }

    /// 登出
    func logout() async {
        await AuthStore.shared.clear()
        isAuthenticated = false
        currentUsername = nil
        UserDefaults.standard.removeObject(forKey: "currentUsername")
    }

    static func makeClient(isDemoMode: Bool) -> APIClientProtocol {
        if isDemoMode { return MockAPIClient() }
        return RealAPIClient(baseURL: URL(string: "http://100.82.235.49:5001")!)
    }

    static func makeDefault() -> AppEnvironment {
        let demo = UserDefaults.standard.object(forKey: "isDemoMode") as? Bool ?? false
        return AppEnvironment(isDemoMode: demo)
    }
}
