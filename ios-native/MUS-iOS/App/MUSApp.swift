import SwiftUI

@main
struct MUSApp: App {
    @StateObject private var environment = AppEnvironment.makeDefault()
    @StateObject private var settings = AppSettings()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(environment)
                .environmentObject(settings)
                .tint(settings.theme.primaryColor)
                .preferredColorScheme(settings.theme.colorScheme)
                .dynamicTypeSize(settings.fontScale.dynamicTypeSize)
        }
    }
}
