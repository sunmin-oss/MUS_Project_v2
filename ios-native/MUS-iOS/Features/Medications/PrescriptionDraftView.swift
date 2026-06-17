import SwiftUI

/// Editable OCR/prescription draft → batch add to medication list
struct PrescriptionDraftView: View {
    @EnvironmentObject private var env: AppEnvironment
    @ObservedObject var store: MedicationStore
    @Environment(\.dismiss) private var dismiss

    enum Phase {
        case pickImage
        case recognizing
        case draft
        case error(String)
    }

    @State private var phase: Phase = .pickImage
    @State private var selectedImage: UIImage?
    @State private var drafts: [DraftItem] = []
    @State private var prescriptionName: String = ""
    @State private var isSaving = false
    @State private var showSuccess = false

    struct DraftItem: Identifiable {
        var id = UUID()
        var drugName: String
        var dosage: String
        var frequency: String
    }

    var body: some View {
        NavigationStack {
            Group {
                switch phase {
                case .pickImage:
                    VStack(spacing: DesignSpacing.lg) {
                        ImagePickerView(selectedImage: $selectedImage)
                            .onChange(of: selectedImage) { newImage in
                                guard let img = newImage else { return }
                                Task { await recognizePrescription(image: img) }
                            }
                    }
                    .padding(DesignSpacing.md)

                case .recognizing:
                    VStack(spacing: DesignSpacing.md) {
                        ProgressView()
                            .scaleEffect(1.5)
                        Text("正在辨識藥單...")
                            .font(DesignTypography.body)
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                    .frame(maxWidth: .infinity, maxHeight: .infinity)

                case .draft:
                    draftListView

                case .error(let msg):
                    VStack(spacing: DesignSpacing.md) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 48))
                            .foregroundStyle(.orange)
                        Text("辨識失敗")
                            .font(DesignTypography.title2)
                        Text(msg)
                            .font(DesignTypography.body)
                            .foregroundStyle(DesignColors.textSecondary)
                            .multilineTextAlignment(.center)
                        Button("重新拍照") {
                            selectedImage = nil
                            phase = .pickImage
                        }
                        .buttonStyle(SpacedButtonStyle(filled: true))
                    }
                    .padding(DesignSpacing.lg)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                }
            }
            .navigationTitle("prescription.draft.title")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("general.cancel") { dismiss() }
                }
                if case .draft = phase {
                    ToolbarItem(placement: .primaryAction) {
                        EditButton()
                    }
                }
            }
            .alert("新增成功", isPresented: $showSuccess) {
                Button("確認") { dismiss() }
            } message: {
                Text("已將 \(drafts.count) 筆藥物加入用藥清單")
            }
        }
    }

    private var draftListView: some View {
        List {
            Section {
                HStack {
                    Image(systemName: "doc.text")
                        .foregroundStyle(DesignColors.primary)
                    TextField("藥單名稱（如：6/17 家醫科）", text: $prescriptionName)
                        .font(DesignTypography.body)
                }
            } header: {
                Text("藥單標籤")
            }

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
    }

    private func recognizePrescription(image: UIImage) async {
        phase = .recognizing
        guard let imageData = image.jpegData(compressionQuality: 0.8) else {
            phase = .error("圖片處理失敗")
            return
        }
        do {
            let result = try await env.apiClient.recognizePrescription(imageData: imageData)
            drafts = result.drugDetails.map { detail in
                DraftItem(
                    drugName: detail.name,
                    dosage: detail.prescriptionInfo?.dosePerTime ?? "1 顆",
                    frequency: detail.prescriptionInfo?.frequency ?? ""
                )
            }
            if drafts.isEmpty && !result.recognizedDrugs.isEmpty {
                drafts = result.recognizedDrugs.map { name in
                    DraftItem(drugName: name, dosage: "", frequency: "")
                }
            }
            phase = drafts.isEmpty ? .error("未能辨識出任何藥物，請重新拍攝清晰的藥單照片") : .draft
        } catch {
            phase = .error(error.localizedDescription)
        }
    }

    private func addAll() {
        isSaving = true
        let profileId = env.selectedProfileId
        Task {
            var successCount = 0
            var lastError: String?
            for draft in drafts where !draft.drugName.trimmingCharacters(in: .whitespaces).isEmpty {
                let label = prescriptionName.trimmingCharacters(in: .whitespaces).isEmpty
                    ? "藥單 \(Date().formatted(date: .abbreviated, time: .omitted))"
                    : prescriptionName.trimmingCharacters(in: .whitespaces)
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
                    notes: "來自處方箋辨識",
                    prescriptionLabel: label
                )
                do {
                    try await store.add(medication: med, apiClient: env.apiClient)
                    successCount += 1
                } catch {
                    print("[PrescriptionDraft] 新增失敗: \(draft.drugName) - \(error.localizedDescription)")
                    lastError = error.localizedDescription
                }
            }
            await store.load(profileId: profileId, apiClient: env.apiClient)
            isSaving = false
            if successCount > 0 {
                showSuccess = true
            } else if let err = lastError {
                phase = .error("新增失敗：\(err)")
            }
        }
    }
}
