import SwiftUI

/// Editable OCR/prescription draft → batch add to medication list
struct PrescriptionDraftView: View {
    @EnvironmentObject private var env: AppEnvironment
    @ObservedObject var store: MedicationStore
    @Environment(\.dismiss) private var dismiss

    @State private var drafts: [DraftItem] = Self.makeMockDrafts()
    @State private var isSaving = false
    @State private var showSuccess = false

    struct DraftItem: Identifiable {
        var id = UUID()
        var drugName: String
        var dosage: String
        var frequency: String
    }

    private static func makeMockDrafts() -> [DraftItem] {
        [
            DraftItem(drugName: "普拿疼 500mg", dosage: "1 顆", frequency: "每日三次"),
            DraftItem(drugName: "維他命 C 1000mg", dosage: "1 顆", frequency: "每日一次"),
            DraftItem(drugName: "胃乳片", dosage: "2 顆", frequency: "三餐飯後")
        ]
    }

    var body: some View {
        NavigationStack {
            List {
                ForEach($drafts) { $draft in
                    Section {
                        HStack {
                            Image(systemName: "pills")
                                .foregroundStyle(DesignColors.primary)
                            TextField("藥品名稱", text: $draft.drugName)
                                .font(DesignTypography.body)
                        }
                        HStack {
                            Image(systemName: "scalemass")
                                .foregroundStyle(DesignColors.textSecondary)
                            TextField("劑量", text: $draft.dosage)
                                .font(DesignTypography.body)
                        }
                        HStack {
                            Image(systemName: "clock")
                                .foregroundStyle(DesignColors.textSecondary)
                            TextField("頻率", text: $draft.frequency)
                                .font(DesignTypography.body)
                        }
                    }
                }
                .onDelete { drafts.remove(atOffsets: $0) }
            }
            .navigationTitle("prescription.draft.title")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("general.cancel") { dismiss() }
                }
                ToolbarItem(placement: .primaryAction) {
                    EditButton()
                }
            }
            .safeAreaInset(edge: .bottom) {
                VStack(spacing: 0) {
                    Divider()
                    PrimaryButton(
                        LocalizedStringKey("prescription.draft.confirm"),
                        systemImage: "plus.circle.fill"
                    ) {
                        addAll()
                    }
                    .disabled(drafts.isEmpty || isSaving)
                    .padding(DesignSpacing.md)
                }
                .background(Color(UIColor.systemBackground))
            }
            .alert("新增成功", isPresented: $showSuccess) {
                Button("確認") { dismiss() }
            } message: {
                Text("已將 \(drafts.count) 筆藥物加入用藥清單")
            }
        }
    }

    private func addAll() {
        isSaving = true
        let profileId = env.selectedProfileId
        Task {
            for draft in drafts where !draft.drugName.trimmingCharacters(in: .whitespaces).isEmpty {
                let med = Medication(
                    id: UUID().uuidString,
                    profileId: profileId,
                    drugName: draft.drugName,
                    dosage: draft.dosage,
                    frequency: draft.frequency,
                    mealTiming: "飯後",
                    nextDoseAt: Date().addingTimeInterval(3600),
                    currentStock: 30,
                    reminderTimes: [],
                    notes: "來自處方箋辨識"
                )
                try? await store.add(medication: med, apiClient: env.apiClient)
            }
            isSaving = false
            showSuccess = true
        }
    }
}
