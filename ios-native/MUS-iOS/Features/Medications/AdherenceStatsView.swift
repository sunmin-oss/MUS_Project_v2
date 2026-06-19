import SwiftUI

struct AdherenceStatsView: View {
    @ObservedObject var store: MedicationStore

    private var weekRate: Double {
        guard !store.medications.isEmpty else { return 0 }
        let rates = store.medications.map { store.adherenceRate(medicationId: $0.id, days: 7) }
        return rates.reduce(0, +) / Double(rates.count)
    }

    private var monthRate: Double {
        guard !store.medications.isEmpty else { return 0 }
        let rates = store.medications.map { store.adherenceRate(medicationId: $0.id, days: 30) }
        return rates.reduce(0, +) / Double(rates.count)
    }

    private var streakDays: Int {
        let cal = Calendar.current
        var streak = 0
        var day = cal.startOfDay(for: Date())
        while true {
            let next = day.addingTimeInterval(86400)
            let dayRecords = store.records.filter { $0.scheduledAt >= day && $0.scheduledAt < next }
            if dayRecords.isEmpty { break }
            let allTaken = dayRecords.allSatisfy { $0.status == .taken }
            if allTaken {
                streak += 1
                day = day.addingTimeInterval(-86400)
            } else {
                break
            }
        }
        return streak
    }

    private var lowestStockMed: Medication? {
        store.medications.min(by: { $0.currentStock < $1.currentStock })
    }

    var body: some View {
        VStack(alignment: .leading, spacing: DesignSpacing.sm) {
            Text("medications.stats.title")
                .font(DesignTypography.title2)
                .padding(.horizontal, DesignSpacing.md)

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: DesignSpacing.sm) {
                statCard(
                    title: NSLocalizedString("medications.stats.week", comment: ""),
                    value: "\(Int(weekRate * 100))%",
                    icon: "calendar.badge.checkmark",
                    color: rateColor(weekRate)
                )
                statCard(
                    title: NSLocalizedString("medications.stats.month", comment: ""),
                    value: "\(Int(monthRate * 100))%",
                    icon: "calendar",
                    color: rateColor(monthRate)
                )
                statCard(
                    title: NSLocalizedString("medications.stats.streak", comment: ""),
                    value: "\(streakDays) 天",
                    icon: "flame.fill",
                    color: streakDays >= 7 ? .orange : DesignColors.primary
                )
                statCard(
                    title: NSLocalizedString("medications.stats.low.stock", comment: ""),
                    value: lowestStockMed.map { "\($0.currentStock.stockDisplay) 顆" } ?? "—",
                    icon: "pills.fill",
                    color: (lowestStockMed?.currentStock ?? 99) <= 7 ? .red : DesignColors.primary
                )
            }
            .padding(.horizontal, DesignSpacing.md)
        }
    }

    @ViewBuilder
    private func statCard(title: String, value: String, icon: String, color: Color) -> some View {
        Card {
            VStack(spacing: DesignSpacing.xs) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(color)
                Text(value)
                    .font(DesignTypography.title2)
                    .fontWeight(.bold)
                Text(title)
                    .font(DesignTypography.caption)
                    .foregroundStyle(DesignColors.textSecondary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, DesignSpacing.xs)
        }
    }

    private func rateColor(_ rate: Double) -> Color {
        if rate >= 0.8 { return .green }
        if rate >= 0.5 { return .orange }
        return .red
    }
}
