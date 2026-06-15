import Foundation
import SwiftUI

/// 全域依賴容器（DI）。所有跨模組服務從此注入。
@MainActor
final class AppEnvironment: ObservableObject {
    @Published var apiClient: APIClientProtocol

    /// Demo 模式：使用 Mock 資料；發佈前可由「我的」分頁切換
    @Published var isDemoMode: Bool {
        didSet {
            UserDefaults.standard.set(isDemoMode, forKey: "isDemoMode")
            apiClient = Self.makeClient(isDemoMode: isDemoMode)
            if !isDemoMode {
                Task { await self.apiClient.bootstrap() }
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
        // 啟動時 bootstrap RealAPIClient（自動 register-or-login）
        if !isDemoMode {
            Task { await self.apiClient.bootstrap() }
        }
    }

    static func makeClient(isDemoMode: Bool) -> APIClientProtocol {
        if isDemoMode { return MockAPIClient() }
        return RealAPIClient(baseURL: URL(string: "http://100.82.235.49:5000")!)
    }

    static func makeDefault() -> AppEnvironment {
        let demo = UserDefaults.standard.object(forKey: "isDemoMode") as? Bool ?? false
        return AppEnvironment(isDemoMode: demo)
    }
}
