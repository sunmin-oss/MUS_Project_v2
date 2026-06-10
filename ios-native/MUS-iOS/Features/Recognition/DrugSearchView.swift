import SwiftUI

/// 藥品名稱搜尋畫面（呼叫 /api/search，可用來驗證後端串接）
struct DrugSearchView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings

    @State private var query: String = ""
    @State private var results: [Drug] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var searchTask: Task<Void, Never>?

    var body: some View {
        VStack(spacing: 0) {
            searchField
                .padding(DesignSpacing.md)

            if isLoading {
                ProgressView().controlSize(.large).padding(.top, 40)
                Spacer()
            } else if let errorMessage {
                errorView(errorMessage)
            } else if results.isEmpty && !query.isEmpty {
                emptyView
            } else {
                resultsList
            }
        }
        .background(settings.theme.backgroundGradient.ignoresSafeArea())
        .navigationTitle(Text(verbatim: "藥物搜尋"))
        .navigationBarTitleDisplayMode(.large)
    }

    private var searchField: some View {
        HStack(spacing: DesignSpacing.sm) {
            Image(systemName: "magnifyingglass")
                .foregroundStyle(DesignColors.textSecondary)
            TextField(text: $query) {
                Text(verbatim: "輸入藥品名稱（中／英文）")
            }
                .textFieldStyle(.plain)
                .autocorrectionDisabled()
                .submitLabel(.search)
                .onSubmit { triggerSearch() }
                .onChange(of: query) { _ in scheduleSearch() }
                .accessibilityIdentifier("search.drug.input")
            if !query.isEmpty {
                Button {
                    query = ""
                    results = []
                    errorMessage = nil
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .foregroundStyle(DesignColors.textSecondary)
                }
                .accessibilityLabel(Text(verbatim: "清除"))
            }
        }
        .padding(DesignSpacing.sm)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color(.secondarySystemBackground))
        )
    }

    private var resultsList: some View {
        List {
            ForEach(results) { drug in
                NavigationLink {
                    DrugDetailView(drugId: drug.id, name: drug.chineseName)
                } label: {
                    VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                        Text(drug.chineseName).font(DesignTypography.body)
                        if let en = drug.englishName, !en.isEmpty {
                            Text(en)
                                .font(DesignTypography.caption)
                                .foregroundStyle(DesignColors.textSecondary)
                        }
                    }
                    .padding(.vertical, DesignSpacing.xs)
                }
                .accessibilityIdentifier("search.drug.row.\(drug.id)")
            }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
    }

    private var emptyView: some View {
        VStack(spacing: DesignSpacing.sm) {
            Spacer().frame(height: 60)
            Image(systemName: "magnifyingglass")
                .font(.system(size: 48))
                .foregroundStyle(DesignColors.textSecondary)
            Text(verbatim: "找不到符合的藥品")
                .font(DesignTypography.body)
                .foregroundStyle(DesignColors.textSecondary)
            Spacer()
        }
    }

    private func errorView(_ message: String) -> some View {
        VStack(spacing: DesignSpacing.sm) {
            Spacer().frame(height: 60)
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 48))
                .foregroundStyle(.orange)
            Text(message)
                .font(DesignTypography.body)
                .foregroundStyle(DesignColors.textSecondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, DesignSpacing.md)
            Button {
                triggerSearch()
            } label: {
                Text(verbatim: "重試")
            }
            .buttonStyle(.borderedProminent)
            Spacer()
        }
    }

    private func scheduleSearch() {
        searchTask?.cancel()
        let current = query
        searchTask = Task {
            try? await Task.sleep(nanoseconds: 350_000_000)
            if Task.isCancelled { return }
            if current == query { await performSearch() }
        }
    }

    private func triggerSearch() {
        searchTask?.cancel()
        Task { await performSearch() }
    }

    @MainActor
    private func performSearch() async {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else {
            results = []
            errorMessage = nil
            isLoading = false
            return
        }
        isLoading = true
        errorMessage = nil
        do {
            let found = try await env.apiClient.searchDrugs(query: trimmed, limit: 20)
            if trimmed == query.trimmingCharacters(in: .whitespacesAndNewlines) {
                results = found
            }
        } catch {
            results = []
            errorMessage = "搜尋失敗，請確認網路或後端連線"
        }
        isLoading = false
    }
}

#Preview {
    NavigationStack {
        DrugSearchView()
            .environmentObject(AppEnvironment.makeDefault())
            .environmentObject(AppSettings())
    }
}
