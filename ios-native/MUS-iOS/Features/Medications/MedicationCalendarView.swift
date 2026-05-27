import SwiftUI
import Charts

struct MedicationCalendarView: View {
    @ObservedObject var store: MedicationStore
    @State private var rangeDays = 7

    private var chartData: [(date: Date, taken: Int, total: Int)] {
        store.recordsByDay(medicationId: nil, days: rangeDays)
    }

    var body: some View {
        ScrollView {
            VStack(spacing: DesignSpacing.md) {
                Picker("", selection: $rangeDays) {
                    Text("7天").tag(7)
                    Text("30天").tag(30)
                }
                .pickerStyle(.segmented)
                .padding(.horizontal, DesignSpacing.md)

                if chartData.allSatisfy({ $0.total == 0 }) {
                    EmptyStateView(
                        titleKey: "medications.empty.title",
                        systemImage: "chart.bar",
                        messageKey: "medications.empty.message"
                    )
                    .frame(minHeight: 200)
                } else {
                    Chart {
                        ForEach(chartData, id: \.date) { item in
                            BarMark(
                                x: .value("日期", item.date, unit: .day),
                                y: .value("服藥率", item.total > 0 ? Double(item.taken) / Double(item.total) : 0)
                            )
                            .foregroundStyle(barColor(taken: item.taken, total: item.total))
                        }
                    }
                    .chartYScale(domain: 0...1)
                    .chartYAxis {
                        AxisMarks(values: [0, 0.5, 0.8, 1.0]) { value in
                            AxisGridLine()
                            AxisValueLabel {
                                if let d = value.as(Double.self) {
                                    Text("\(Int(d * 100))%")
                                }
                            }
                        }
                    }
                    .chartXAxis {
                        AxisMarks(values: .stride(by: .day)) { _ in
                            AxisGridLine()
                            AxisValueLabel(format: .dateTime.day(), centered: true)
                        }
                    }
                    .frame(height: 220)
                    .padding(DesignSpacing.md)
                }

                AdherenceStatsView(store: store)
            }
        }
        .navigationTitle("medications.calendar.title")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func barColor(taken: Int, total: Int) -> Color {
        guard total > 0 else { return .gray.opacity(0.3) }
        let rate = Double(taken) / Double(total)
        if rate >= 0.8 { return .green }
        if rate >= 0.5 { return .orange }
        return .red
    }
}
