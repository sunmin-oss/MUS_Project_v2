import SwiftUI

/// 藥物預覽詳情頁
struct MedicationDetailView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings
    @ObservedObject var store: MedicationStore

    let medication: Medication

    @State private var drug: Drug?
    @State private var alerts: [SafetyAlert] = []
    @State private var isLoadingDrug = false
    @State private var showEditSheet = false

    private var todayTaken: Int {
        let start = Calendar.current.startOfDay(for: Date())
        return store.records.filter {
            $0.medicationId == medication.id
            && $0.status == .taken
            && $0.scheduledAt >= start
        }.count
    }

    private var dailyLimit: Int {
        if let match = medication.frequency.range(of: "[0-9]+", options: .regularExpression) {
            return Int(medication.frequency[match]) ?? 1
        }
        return 1
    }

    var body: some View {
        ScrollView {
            VStack(spacing: DesignSpacing.md) {
                headerCard
                usageCard
                stockCard
                if !alerts.isEmpty {
                    safetyCard
                }
                if let drug {
                    drugInfoCard(drug)
                }
            }
            .padding(DesignSpacing.md)
        }
        .background(settings.theme.backgroundGradient.ignoresSafeArea())
        .navigationTitle(drug?.chineseName ?? medication.drugName)
        .navigationBarTitleDisplayMode(.large)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    showEditSheet = true
                } label: {
                    Text("編輯")
                }
            }
        }
        .sheet(isPresented: $showEditSheet, onDismiss: {
            Task { await store.load(profileId: medication.profileId, apiClient: env.apiClient) }
        }) {
            AddMedicationView(store: store, editingMedication: medication)
        }
        .task { await loadDrugInfo() }
    }

    // MARK: - Header

    private var headerCard: some View {
        Card {
            HStack(spacing: DesignSpacing.md) {
                if let drug, drug.imageURL != nil {
                    DrugThumb(url: drug.imageURL, size: 72)
                } else {
                    ZStack {
                        RoundedRectangle(cornerRadius: 14, style: .continuous)
                            .fill(DesignColors.primary.opacity(0.12))
                        Image(systemName: "pills.fill")
                            .font(.system(size: 28))
                            .foregroundStyle(DesignColors.primary)
                    }
                    .frame(width: 72, height: 72)
                }

                VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                    Text(drug?.chineseName ?? medication.drugName)
                        .font(DesignTypography.title2)

                    if let en = drug?.englishName, !en.isEmpty {
                        Text(en)
                            .font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                    } else if drug?.chineseName != nil {
                        // 有中文名時把原始 drugName (英文) 也顯示
                        let originalName = medication.drugName
                        if originalName != drug?.chineseName {
                            Text(originalName)
                                .font(DesignTypography.caption)
                                .foregroundStyle(DesignColors.textSecondary)
                        }
                    }

                    if let lic = drug?.licenseNumber, !lic.isEmpty {
                        Text(lic)
                            .font(.system(size: 11))
                            .foregroundStyle(DesignColors.textSecondary)
                    }

                    if let label = medication.prescriptionLabel, !label.isEmpty {
                        HStack(spacing: 4) {
                            Image(systemName: "doc.text")
                                .font(.system(size: 11))
                            Text(label)
                                .font(.system(size: 12))
                        }
                        .foregroundStyle(DesignColors.primary)
                        .padding(.top, 2)
                    }
                }
                Spacer()
            }
        }
    }

    // MARK: - Usage Card

    private var usageCard: some View {
        Card {
            VStack(spacing: 0) {
                infoRow(icon: "scalemass", title: "劑量", value: medication.dosage)
                Divider().padding(.leading, 40)
                infoRow(icon: "clock", title: "頻率", value: medication.frequency)
                Divider().padding(.leading, 40)
                infoRow(icon: "fork.knife", title: "用餐時間", value: medication.mealTiming)
                Divider().padding(.leading, 40)
                infoRow(icon: "bell", title: "下次服藥",
                        value: medication.nextDoseAt.formatted(date: .abbreviated, time: .shortened))
                if !medication.notes.isEmpty && medication.notes != "來自處方箋辨識" {
                    Divider().padding(.leading, 40)
                    infoRow(icon: "note.text", title: "備註", value: medication.notes)
                }
            }
        }
    }

    // MARK: - Stock Card

    private var stockCard: some View {
        Card {
            HStack(spacing: DesignSpacing.md) {
                stockGauge
                VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                    Text("庫存狀態")
                        .font(DesignTypography.headline)
                    Text("剩餘 \(medication.currentStock.stockDisplay) 顆")
                        .font(DesignTypography.body)
                        .foregroundStyle(medication.isStockLow ? .red : DesignColors.textPrimary)
                    Text("今日已服 \(todayTaken) / \(dailyLimit) 次")
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                    if medication.currentStock > 0 && dailyLimit > 0 {
                        Text("預估可服用 \(medication.daysRemaining) 天")
                            .font(DesignTypography.caption)
                            .foregroundStyle(medication.daysRemaining <= 3 ? .orange : DesignColors.textSecondary)
                    }
                }
                Spacer()
            }
        }
    }

    @ViewBuilder
    private var stockGauge: some View {
        let total = max(medication.currentStock, 1.0)
        let fraction = min(medication.currentStock / max(total, 1.0), 1.0)
        ZStack {
            Circle()
                .stroke(Color.gray.opacity(0.15), lineWidth: 6)
            Circle()
                .trim(from: 0, to: fraction)
                .stroke(medication.isStockLow ? Color.red : DesignColors.primary,
                        style: StrokeStyle(lineWidth: 6, lineCap: .round))
                .rotationEffect(.degrees(-90))
            Text(medication.currentStock.stockDisplay)
                .font(.system(size: 18, weight: .bold, design: .rounded))
                .foregroundStyle(medication.isStockLow ? .red : DesignColors.primary)
        }
        .frame(width: 64, height: 64)
    }

    // MARK: - Safety Card

    private var safetyCard: some View {
        VStack(alignment: .leading, spacing: DesignSpacing.sm) {
            Label("安全提醒", systemImage: "exclamationmark.triangle.fill")
                .font(DesignTypography.headline)
                .foregroundStyle(.orange)
            ForEach(alerts) { alert in
                HStack(alignment: .top, spacing: 8) {
                    Circle()
                        .fill(alertColor(alert.level))
                        .frame(width: 8, height: 8)
                        .padding(.top, 6)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(alert.title)
                            .font(DesignTypography.body)
                        Text(alert.message)
                            .font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                }
            }
        }
        .padding(DesignSpacing.md)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(Color.orange.opacity(0.06))
        )
    }

    // MARK: - Drug Info Card

    @ViewBuilder
    private func drugInfoCard(_ drug: Drug) -> some View {
        VStack(alignment: .leading, spacing: DesignSpacing.sm) {
            Text("藥品資訊")
                .font(DesignTypography.headline)
            Card {
                VStack(spacing: 0) {
                    if let shape = drug.shape, !shape.isEmpty {
                        detailRow("外觀", value: shape)
                        Divider().padding(.leading, 12)
                    }
                    if let color = drug.color, !color.isEmpty {
                        detailRow("顏色", value: color)
                        Divider().padding(.leading, 12)
                    }
                    if let usage = drug.usage, !usage.isEmpty {
                        detailRow("適應症", value: usage)
                    }
                }
            }
        }
    }

    // MARK: - Helpers

    private func infoRow(icon: String, title: String, value: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundStyle(DesignColors.primary)
                .frame(width: 24)
            Text(title)
                .font(DesignTypography.body)
                .foregroundStyle(DesignColors.textSecondary)
                .frame(width: 72, alignment: .leading)
            Text(value.isEmpty ? "—" : value)
                .font(DesignTypography.body)
            Spacer()
        }
        .padding(.vertical, DesignSpacing.sm)
    }

    private func detailRow(_ title: String, value: String) -> some View {
        HStack {
            Text(title)
                .font(DesignTypography.body)
                .foregroundStyle(DesignColors.textSecondary)
                .frame(width: 60, alignment: .leading)
            Text(value)
                .font(DesignTypography.body)
            Spacer()
        }
        .padding(.vertical, DesignSpacing.sm)
    }

    private func alertColor(_ level: SafetyAlert.Level) -> Color {
        switch level {
        case .contraindicated: return .red
        case .major: return .orange
        case .moderate: return .yellow
        case .minor: return .blue
        }
    }

    private func loadDrugInfo() async {
        isLoadingDrug = true
        defer { isLoadingDrug = false }

        // 嘗試用藥名搜尋資料庫取得藥品詳情，若全名搜不到則逐步縮短關鍵字
        let queries = Self.searchQueries(for: medication.drugName)
        for query in queries {
            do {
                let results = try await env.apiClient.searchDrugs(query: query, limit: 1)
                if let first = results.first {
                    drug = first
                    let safetyResults = try? await env.apiClient.checkSafety(
                        profileId: medication.profileId,
                        drugIds: [first.id]
                    )
                    alerts = safetyResults ?? []
                    return
                }
            } catch {
                continue
            }
        }
    }

    /// 產生多個搜尋關鍵字：全名 → 去掉品牌名 → 取核心藥名
    static func searchQueries(for name: String) -> [String] {
        var queries = [name]
        // 去掉「」引號和括號品牌名
        let cleaned = name
            .replacingOccurrences(of: "\"", with: "")
            .replacingOccurrences(of: "\u{201C}", with: "")
            .replacingOccurrences(of: "\u{201D}", with: "")
        if cleaned != name { queries.append(cleaned) }

        // 去掉常見劑型後綴取核心名（膠囊、錠、糖衣錠、膜衣錠、散、液 etc.）
        let forms = ["膜衣錠", "糖衣錠", "咀嚼錠", "膠囊", "錠", "散", "乳膏", "軟膏"]
        for form in forms {
            if cleaned.hasSuffix(form) {
                let core = String(cleaned.dropLast(form.count))
                if !core.isEmpty && core != cleaned { queries.append(core) }
                break
            }
        }

        // 英文名逐步縮短（去尾部單詞）
        let words = cleaned.split(separator: " ").map(String.init)
        if words.count > 1 {
            for len in stride(from: words.count - 1, through: 1, by: -1) {
                let partial = words.prefix(len).joined(separator: " ")
                if !queries.contains(partial) { queries.append(partial) }
            }
        }
        // 也嘗試用 . 和 - 分割取核心（如 "T.F.SU-MIN" → "SU-MIN"）
        let parts = cleaned.components(separatedBy: CharacterSet(charactersIn: ".-"))
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { $0.count >= 2 }
        for part in parts where !queries.contains(part) {
            queries.append(part)
        }

        return queries
    }
}
