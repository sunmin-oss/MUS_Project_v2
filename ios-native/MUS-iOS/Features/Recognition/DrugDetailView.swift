import SwiftUI

/// 藥品詳情頁（從辨識結果或搜尋進入）
struct DrugDetailView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings

    let drugId: Int
    let name: String

    @State private var drug: Drug?
    @State private var alerts: [SafetyAlert] = []
    @State private var isLoading = true

    var body: some View {
        ScrollView {
            VStack(spacing: DesignSpacing.md) {
                if isLoading {
                    ProgressView().controlSize(.large).padding(.top, 60)
                } else if let drug {
                    drugHeader(drug)
                    if !alerts.isEmpty {
                        safetySection(alerts)
                    }
                    infoSection(drug)
                }
            }
            .padding(DesignSpacing.md)
        }
        .background(settings.theme.backgroundGradient.ignoresSafeArea())
        .navigationTitle(name)
        .navigationBarTitleDisplayMode(.large)
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        async let drugResult = try? env.apiClient.fetchDrug(id: drugId)
        async let alertsResult = try? env.apiClient.checkSafety(profileId: "p1", drugIds: [drugId])
        drug = await drugResult
        alerts = await alertsResult ?? []
        isLoading = false
    }

    @ViewBuilder
    private func drugHeader(_ drug: Drug) -> some View {
        Card {
            HStack(spacing: DesignSpacing.md) {
                Image(systemName: "pills.fill")
                    .font(.system(size: 48))
                    .foregroundStyle(settings.theme.primaryColor)
                VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                    Text(drug.chineseName).font(DesignTypography.title)
                    if let en = drug.englishName {
                        Text(en).font(DesignTypography.body)
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                    if let lic = drug.licenseNumber {
                        Text(lic).font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func safetySection(_ alerts: [SafetyAlert]) -> some View {
        VStack(alignment: .leading, spacing: DesignSpacing.sm) {
            Text("drug.section.safety").font(DesignTypography.title2)
            ForEach(alerts) { alert in
                AlertBanner(level: bannerLevel(alert.level),
                             titleKey: LocalizedStringKey(alert.title),
                             messageKey: LocalizedStringKey(alert.message))
            }
        }
    }

    @ViewBuilder
    private func infoSection(_ drug: Drug) -> some View {
        VStack(alignment: .leading, spacing: DesignSpacing.sm) {
            Text("drug.section.info").font(DesignTypography.title2)
            Card {
                VStack(spacing: 0) {
                    infoRow("drug.shape", value: drug.shape)
                    Divider()
                    infoRow("drug.color", value: drug.color)
                    Divider()
                    infoRow("drug.usage", value: drug.usage)
                }
            }
        }
    }

    private func infoRow(_ key: LocalizedStringKey, value: String?) -> some View {
        HStack {
            Text(key).font(DesignTypography.body)
                .foregroundStyle(DesignColors.textSecondary)
                .frame(width: 80, alignment: .leading)
            Text(value ?? NSLocalizedString("drug.info.unknown", comment: ""))
                .font(DesignTypography.body)
            Spacer()
        }
        .padding(.vertical, DesignSpacing.sm)
    }

    private func bannerLevel(_ level: SafetyAlert.Level) -> AlertBanner.Level {
        switch level {
        case .contraindicated: return .critical
        case .major: return .major
        case .moderate: return .moderate
        case .minor: return .minor
        }
    }
}

#Preview {
    NavigationStack {
        DrugDetailView(drugId: 101, name: "普拿疼")
            .environmentObject(AppEnvironment.makeDefault())
            .environmentObject(AppSettings())
    }
}
