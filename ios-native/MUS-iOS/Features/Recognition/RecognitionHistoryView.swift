import SwiftUI

// MARK: - History Store (in-memory; Phase 3 接 API / Core Data 時替換)

/// W2 階段先以 @MainActor class 儲存記憶體版本歷史。
/// 待 Xcode 中建立 MUSData.xcdatamodeld 後，可無縫換成 Core Data。
@MainActor
final class RecognitionHistoryStore: ObservableObject {
    @Published private(set) var records: [HistoryRecord] = []

    struct HistoryRecord: Identifiable {
        let id = UUID()
        let timestamp: Date
        let thumbnail: UIImage?
        let topResultName: String
        let confidence: Double
        let drugId: Int
    }

    func append(image: UIImage?, result: RecognitionResult) {
        guard let item = result.items.first else { return }
        let record = HistoryRecord(
            timestamp: Date(),
            thumbnail: image.map { resized($0, to: CGSize(width: 80, height: 80)) },
            topResultName: item.name,
            confidence: item.confidence,
            drugId: item.drugId
        )
        records.insert(record, at: 0)
    }

    func delete(at offsets: IndexSet) {
        records.remove(atOffsets: offsets)
    }

    private func resized(_ image: UIImage, to size: CGSize) -> UIImage {
        UIGraphicsImageRenderer(size: size).image { _ in
            image.draw(in: CGRect(origin: .zero, size: size))
        }
    }
}

// MARK: - History View

struct RecognitionHistoryView: View {
    @EnvironmentObject private var settings: AppSettings
    @StateObject private var store = RecognitionHistoryStore()

    var body: some View {
        NavigationStack {
            Group {
                if store.records.isEmpty {
                    EmptyStateView(titleKey: "history.empty.title",
                                   systemImage: "clock.arrow.circlepath",
                                   messageKey: "history.empty.message")
                } else {
                    List {
                        ForEach(store.records) { record in
                            NavigationLink(destination: DrugDetailView(
                                drugId: record.drugId,
                                name: record.topResultName
                            )) {
                                HistoryRow(record: record)
                            }
                        }
                        .onDelete { store.delete(at: $0) }
                    }
                    .listStyle(.insetGrouped)
                }
            }
            .navigationTitle("history.title")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                if !store.records.isEmpty {
                    EditButton()
                }
            }
        }
    }
}

private struct HistoryRow: View {
    let record: RecognitionHistoryStore.HistoryRecord

    var body: some View {
        HStack(spacing: DesignSpacing.md) {
            Group {
                if let img = record.thumbnail {
                    Image(uiImage: img)
                        .resizable().scaledToFill()
                } else {
                    Image(systemName: "photo")
                        .foregroundStyle(DesignColors.textSecondary)
                }
            }
            .frame(width: 56, height: 56)
            .clipShape(RoundedRectangle(cornerRadius: DesignRadius.sm))
            .background(Color(.secondarySystemBackground))

            VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                Text(record.topResultName).font(DesignTypography.headline)
                Text(record.timestamp.formatted(date: .abbreviated, time: .shortened))
                    .font(DesignTypography.caption)
                    .foregroundStyle(DesignColors.textSecondary)
                Text(String(format: "%.0f%%", record.confidence * 100) + " " +
                     NSLocalizedString("recognition.confidence", comment: ""))
                    .font(DesignTypography.caption)
                    .foregroundStyle(DesignColors.textSecondary)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    RecognitionHistoryView()
        .environmentObject(AppSettings())
}
