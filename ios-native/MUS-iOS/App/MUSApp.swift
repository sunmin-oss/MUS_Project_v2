import SwiftUI

@main
struct MUSApp: App {
    @StateObject private var environment = AppEnvironment.makeDefault()
    @StateObject private var settings = AppSettings()

    init() {
        if CommandLine.arguments.contains("--demo-mode") {
            UserDefaults.standard.set(true, forKey: "isDemoMode")
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
