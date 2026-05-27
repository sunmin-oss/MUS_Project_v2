import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings
    @State private var showRecognition = false
    @State private var showHistory = false
    @State private var showPrescriptionDraft = false
    @StateObject private var prescriptionStore = MedicationStore()

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
                                  tint: settings.theme.primaryColor) {
                        showRecognition = true
                    }
                    PrimaryButton("home.action.prescription",
                                  systemImage: "doc.text.viewfinder",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {
                        showPrescriptionDraft = true
                    }
                    PrimaryButton("home.action.history",
                                  systemImage: "clock.arrow.circlepath",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {
                        showHistory = true
                    }
                    PrimaryButton("home.action.search",
                                  systemImage: "magnifyingglass",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {}
                }
                .padding(DesignSpacing.md)
            }
            .background(settings.theme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("tab.home")
            .navigationDestination(isPresented: $showRecognition) {
                RecognitionView()
            }
            .navigationDestination(isPresented: $showHistory) {
                RecognitionHistoryView()
            }
            .sheet(isPresented: $showPrescriptionDraft) {
                PrescriptionDraftView(store: prescriptionStore)
            }
        }
    }
}

#Preview {
    HomeView()
        .environmentObject(AppEnvironment.makeDefault())
        .environmentObject(AppSettings())
}
