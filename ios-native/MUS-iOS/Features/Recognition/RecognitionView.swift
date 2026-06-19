import SwiftUI

/// 辨識主流程：選圖 → 預處理 → 上傳辨識 → 結果
struct RecognitionView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings
    @ObservedObject var historyStore: RecognitionHistoryStore

    @State private var selectedImage: UIImage?
    @State private var phase: Phase = .idle

    enum Phase: Equatable {
        case idle
        case preprocessing
        case uploading
        case result([RecognitionItem])
        case error(String)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: DesignSpacing.lg) {
                    ImagePickerView(selectedImage: $selectedImage)
                        .onChange(of: selectedImage) { newImage in
                            guard let img = newImage else { phase = .idle; return }
                            Task { await run(image: img) }
                        }

                    switch phase {
                    case .idle:
                        EmptyView()
                    case .preprocessing:
                        StatusCard(icon: "wand.and.stars", titleKey: "recognition.status.preprocessing")
                    case .uploading:
                        StatusCard(icon: "arrow.up.circle.fill", titleKey: "recognition.status.uploading")
                    case .result(let items) where items.isEmpty:
                        EmptyStateView(titleKey: "recognition.result.empty.title",
                                       systemImage: "questionmark.circle",
                                       messageKey: "recognition.result.empty.message")
                    case .result(let items):
                        VStack(alignment: .leading, spacing: DesignSpacing.sm) {
                            Text("recognition.result.title")
                                .font(DesignTypography.title2)
                            ForEach(items) { item in
                                NavigationLink(destination: DrugDetailView(drugId: item.drugId,
                                                                            name: item.name)) {
                                    RecognitionResultRow(item: item)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    case .error(let msg):
                        AlertBanner(level: .major,
                                    titleKey: "recognition.error.title",
                                    messageKey: LocalizedStringKey(msg))

                        Button {
                            guard let img = selectedImage else { return }
                            Task { await run(image: img) }
                        } label: {
                            Label("重新辨識", systemImage: "arrow.clockwise")
                                .font(DesignTypography.body.bold())
                                .frame(maxWidth: .infinity)
                                .padding(DesignSpacing.md)
                                .background(DesignColors.primary)
                                .foregroundStyle(.white)
                                .clipShape(RoundedRectangle(cornerRadius: DesignSpacing.sm))
                        }
                    }
                }
                .padding(DesignSpacing.md)
            }
            .background(settings.theme.backgroundGradient.ignoresSafeArea())
            .navigationTitle("home.action.recognize")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func run(image: UIImage) async {
        phase = .preprocessing
        let processed = await ImageProcessor.process(image)
        guard let data = processed.jpegData(compressionQuality: 0.8) else {
            phase = .error("recognition.error.compress"); return
        }

        phase = .uploading
        do {
            let result = try await env.apiClient.recognizeDrug(imageData: data)
            phase = .result(result.items)
            // 存入辨識歷史
            historyStore.append(image: image, result: result)
        } catch {
            phase = .error(error.localizedDescription)
        }
    }
}

// MARK: - 子元件

private struct StatusCard: View {
    let icon: String
    let titleKey: LocalizedStringKey

    var body: some View {
        Card {
            HStack(spacing: DesignSpacing.md) {
                ProgressView().controlSize(.regular)
                Image(systemName: icon).foregroundStyle(DesignColors.primary)
                Text(titleKey).font(DesignTypography.body)
            }
        }
    }
}

struct RecognitionResultRow: View {
    let item: RecognitionItem
    var showChevron = true

    var body: some View {
        Card {
            HStack(spacing: DesignSpacing.md) {
                Image(systemName: "pills.circle.fill")
                    .font(.system(size: 36))
                    .foregroundStyle(DesignColors.primary)
                VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                    Text(item.name).font(DesignTypography.title2)
                    Text(String(format: "%.0f%%", item.confidence * 100) + " " +
                         NSLocalizedString("recognition.confidence", comment: ""))
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                }
                Spacer()
                if showChevron {
                    Image(systemName: "chevron.right")
                        .foregroundStyle(DesignColors.textSecondary)
                }
            }
        }
    }
}

#Preview {
    RecognitionView(historyStore: RecognitionHistoryStore())
        .environmentObject(AppEnvironment.makeDefault())
        .environmentObject(AppSettings())
}
