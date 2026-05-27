import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings
    @State private var showRecognition = false
    @State private var showHistory = false
    @State private var showPrescriptionDraft = false
    @State private var showPharmacy = false
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
                    .accessibilityLabel(Text("home.action.recognize"))
                    .accessibilityIdentifier("home.action.recognize")

                    PrimaryButton("home.action.prescription",
                                  systemImage: "doc.text.viewfinder",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {
                        showPrescriptionDraft = true
                    }
                    .accessibilityLabel(Text("home.action.prescription"))
                    .accessibilityIdentifier("home.action.prescription")

                    PrimaryButton("home.action.history",
                                  systemImage: "clock.arrow.circlepath",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {
                        showHistory = true
                    }
                    .accessibilityLabel(Text("home.action.history"))
                    .accessibilityIdentifier("home.action.history")

                    PrimaryButton("home.action.pharmacy",
                                  systemImage: "mappin.and.ellipse",
                                  style: .bordered,
                                  tint: settings.theme.primaryColor) {
                        showPharmacy = true
                    }
                    .accessibilityLabel(Text("home.action.pharmacy"))
                    .accessibilityIdentifier("home.action.pharmacy")
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
            .navigationDestination(isPresented: $showPharmacy) {
                PharmacyMapView()
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
