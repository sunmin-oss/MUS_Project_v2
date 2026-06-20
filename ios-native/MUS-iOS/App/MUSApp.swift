import SwiftUI

@main
struct MUSApp: App {
    @StateObject private var environment = AppEnvironment.makeDefault()
    @StateObject private var settings = AppSettings()

    init() {
        if CommandLine.arguments.contains("--demo-mode") {
            UserDefaults.standard.set(true, forKey: "isDemoMode")
        } else if CommandLine.arguments.contains("--uitesting") {
            // 非 demo 測試模式：確保 isDemoMode 被清除
            UserDefaults.standard.set(false, forKey: "isDemoMode")
        }
    }

    var body: some Scene {
        WindowGroup {
            Group {
                if environment.isAuthenticated {
                    RootView()
                } else {
                    LoginView()
                }
            }
            .environmentObject(environment)
            .environmentObject(settings)
            .tint(settings.theme.primaryColor)
            .preferredColorScheme(settings.theme.colorScheme)
            .dynamicTypeSize(settings.fontScale.dynamicTypeSize)
        }
    }
}
