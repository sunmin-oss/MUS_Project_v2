import SwiftUI

// MARK: - History Store（LocalCache 持久化）

@MainActor
final class RecognitionHistoryStore: ObservableObject {
    @Published private(set) var records: [HistoryRecord] = []

    struct HistoryRecord: Identifiable, Codable {
        let id: UUID
        let timestamp: Date
        let topResultName: String
        let confidence: Double
        let drugId: Int
        /// 縮圖 JPEG Data（可選）
        let thumbnailData: Data?

        init(id: UUID = UUID(), timestamp: Date = Date(), topResultName: String, confidence: Double, drugId: Int, thumbnailData: Data? = nil) {
            self.id = id
            self.timestamp = timestamp
            self.topResultName = topResultName
            self.confidence = confidence
            self.drugId = drugId
            self.thumbnailData = thumbnailData
        }

        var thumbnail: UIImage? {
            thumbnailData.flatMap { UIImage(data: $0) }
        }
    }

    private let cacheKey = "recognition_history"
    private let maxCount = 50

    init() {
        records = LocalCache.load([HistoryRecord].self, forKey: cacheKey) ?? []
    }

    func append(image: UIImage?, result: RecognitionResult) {
        guard let item = result.items.first else { return }
        let thumbData = image.flatMap {
            resized($0, to: CGSize(width: 80, height: 80)).jpegData(compressionQuality: 0.6)
        }
        let record = HistoryRecord(
            topResultName: item.name,
            confidence: item.confidence,
            drugId: item.drugId,
            thumbnailData: thumbData
        )
        records.insert(record, at: 0)
        if records.count > maxCount {
            records = Array(records.prefix(maxCount))
        }
        save()
    }

    func delete(at offsets: IndexSet) {
        records.remove(atOffsets: offsets)
        save()
    }

    func clearAll() {
        records.removeAll()
        LocalCache.remove(forKey: cacheKey)
    }

    private func save() {
        LocalCache.save(records, forKey: cacheKey)
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
    @ObservedObject var store: RecognitionHistoryStore

    var body: some View {
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
                ToolbarItem(placement: .navigationBarTrailing) {
                    Menu {
                        Button(role: .destructive) {
                            store.clearAll()
                        } label: {
                            Label("清除全部紀錄", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
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
    NavigationStack {
        RecognitionHistoryView(store: RecognitionHistoryStore())
            .environmentObject(AppSettings())
    }
}
