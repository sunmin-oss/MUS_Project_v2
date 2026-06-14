import Foundation
import SwiftUI

/// 全域依賴容器（DI）。所有跨模組服務從此注入。
@MainActor
final class AppEnvironment: ObservableObject {
    let apiClient: APIClientProtocol

    /// Demo 模式：使用 Mock 資料；發佈前可由「我的」分頁切換
    @Published var isDemoMode: Bool {
        didSet { UserDefaults.standard.set(isDemoMode, forKey: "isDemoMode") }
    }

    /// 目前選取的成員 profileId（跨頁面同步）
    @Published var selectedProfileId: String {
        didSet { UserDefaults.standard.set(selectedProfileId, forKey: "selectedProfileId") }
    }

    init(apiClient: APIClientProtocol, isDemoMode: Bool) {
        self.apiClient = apiClient
        self.isDemoMode = isDemoMode
        self.selectedProfileId = UserDefaults.standard.string(forKey: "selectedProfileId") ?? "p1"
    }

    static func makeDefault() -> AppEnvironment {
        let demo = UserDefaults.standard.object(forKey: "isDemoMode") as? Bool ?? true
        // W1 階段一律使用 MockAPIClient；Phase 3 接 API 時改注入 RealAPIClient
        let client: APIClientProtocol = MockAPIClient()
        return AppEnvironment(apiClient: client, isDemoMode: demo)
    }
}
