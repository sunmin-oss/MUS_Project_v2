import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: DesignSpacing.md) {
                    if env.isDemoMode {
                        AlertBanner(level: .minor,
                                    titleKey: "demo.mode.title",
                                    messageKey: "demo.mode.message")
                    }

                    Card {
                        VStack(alignment: .leading, spacing: DesignSpacing.sm) {
                            Text("home.welcome.title").font(DesignTypography.title)
                            Text("home.welcome.subtitle")
                                .font(DesignTypography.body)
                                .foregroundStyle(DesignColors.textSecondary)
                        }
                    }

                    PrimaryButton("home.action.recognize", systemImage: "camera.fill",
                                  tint: settings.theme.primaryColor) {}
                    PrimaryButton("home.action.prescription",
                                  systemImage: "doc.text.viewfinder",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {}
                    PrimaryButton("home.action.search",
                                  systemImage: "magnifyingglass",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {}
                }
                .padding(DesignSpacing.md)
            }
            .background(settings.theme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("tab.home")
        }
    }
}

#Preview {
    HomeView()
        .environmentObject(AppEnvironment.makeDefault())
        .environmentObject(AppSettings())
}
