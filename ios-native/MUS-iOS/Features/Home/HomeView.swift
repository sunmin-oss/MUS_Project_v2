import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings
    @State private var showRecognition = false
    @State private var showHistory = false
    @State private var showPrescriptionDraft = false
    @State private var showPharmacy = false
    @State private var showSearch = false
    @EnvironmentObject private var prescriptionStore: MedicationStore
    @StateObject private var serverStatus = ServerStatusChecker(baseURL: URL(string: "http://100.82.235.49:5001")!)
    @StateObject private var recognitionHistory = RecognitionHistoryStore()

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
                            HStack {
                                Text("home.welcome.title").font(DesignTypography.title)
                                Spacer()
                                serverStatusBadge
                            }
                            Text("home.welcome.subtitle")
                                .font(DesignTypography.body)
                                .foregroundStyle(DesignColors.textSecondary)
                        }
                    }

                    // AI 資訊免責提示
                    HStack(alignment: .top, spacing: 8) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 13))
                            .foregroundStyle(.orange)
                        Text("本 App 含有 AI 生成內容，可能存在錯誤或不完整資訊。用藥決策請以專業醫療人員建議為準。")
                            .font(.system(size: 12))
                            .foregroundStyle(DesignColors.textSecondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    .padding(.horizontal, 12)
                    .padding(.vertical, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.orange.opacity(0.06))
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.orange.opacity(0.2), lineWidth: 0.5)
                            )
                    )

                    homeBtn("home.action.recognize", icon: "camera.fill", filled: true) {
                        showRecognition = true
                    }
                    homeBtn("home.action.search", icon: "magnifyingglass", filled: false) {
                        showSearch = true
                    }
                    homeBtn("home.action.prescription", icon: "doc.text.viewfinder", filled: false) {
                        showPrescriptionDraft = true
                    }
                    homeBtn("home.action.history", icon: "clock.arrow.circlepath", filled: false) {
                        showHistory = true
                    }
                    homeBtn("home.action.pharmacy", icon: "mappin.and.ellipse", filled: false) {
                        showPharmacy = true
                    }
                }
                .padding(DesignSpacing.md)
            }
            .background(settings.theme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("tab.home")
            .onAppear { serverStatus.startMonitoring() }
            .onDisappear { serverStatus.stopMonitoring() }
            .navigationDestination(isPresented: $showRecognition) { RecognitionView(historyStore: recognitionHistory) }
            .navigationDestination(isPresented: $showHistory) { RecognitionHistoryView(store: recognitionHistory) }
            .navigationDestination(isPresented: $showPharmacy) { PharmacyMapView() }
            .navigationDestination(isPresented: $showSearch) { DrugSearchView() }
            .sheet(isPresented: $showPrescriptionDraft) {
                PrescriptionDraftView(store: prescriptionStore)
            }
        }
    }

    private var serverStatusBadge: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(serverStatus.isOnline ? Color.green : Color.red)
                .frame(width: 8, height: 8)
            Text(serverStatus.isOnline ? "伺服器連線中" : "伺服器離線")
                .font(.system(size: 12))
                .foregroundStyle(serverStatus.isOnline ? .green : .red)
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 4)
        .background(
            Capsule()
                .fill(serverStatus.isOnline ? Color.green.opacity(0.1) : Color.red.opacity(0.1))
        )
        .onTapGesture { serverStatus.check() }
    }

    private func homeBtn(_ titleKey: String, icon: String, filled: Bool,
                         action: @escaping () -> Void) -> some View {
        let tint = settings.theme.primaryColor
        return Button(action: action) {
            SpacedButtonLabel(text: NSLocalizedString(titleKey, comment: ""),
                              systemImage: icon)
        }
        .buttonStyle(SpacedButtonStyle(filled: filled, tint: tint))
        .accessibilityIdentifier(titleKey)
    }
}

#Preview {
    let env = AppEnvironment.makeDefault()
    return HomeView()
        .environmentObject(env)
        .environmentObject(env.medicationStore)
        .environmentObject(AppSettings())
}
