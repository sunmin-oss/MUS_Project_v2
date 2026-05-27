import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var env: AppEnvironment

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

                    PrimaryButton("home.action.recognize", systemImage: "camera.fill") {}
                    PrimaryButton("home.action.prescription",
                                  systemImage: "doc.text.viewfinder",
                                  style: .bordered) {}
                    PrimaryButton("home.action.search",
                                  systemImage: "magnifyingglass",
                                  style: .bordered) {}
                }
                .padding(DesignSpacing.md)
            }
            .background(DesignColors.background)
            .navigationTitle("tab.home")
        }
    }
}

#Preview {
    HomeView().environmentObject(AppEnvironment.makeDefault())
}
