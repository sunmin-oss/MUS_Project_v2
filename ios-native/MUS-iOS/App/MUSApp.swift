import SwiftUI

@main
struct MUSApp: App {
    @StateObject private var environment = AppEnvironment.makeDefault()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(environment)
                .tint(DesignColors.primary)
        }
    }
}
