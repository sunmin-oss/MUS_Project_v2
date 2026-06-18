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
        var days: Int?
        var totalQuantity: String?
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
                    frequency: detail.prescriptionInfo?.frequency ?? "",
                    days: detail.prescriptionInfo?.days,
                    totalQuantity: detail.prescriptionInfo?.totalQuantity
                )
            }
            if drafts.isEmpty && !result.recognizedDrugs.isEmpty {
                drafts = result.recognizedDrugs.map { name in
                    DraftItem(drugName: name, dosage: "", frequency: "", days: nil, totalQuantity: nil)
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
            let label = prescriptionName.trimmingCharacters(in: .whitespaces).isEmpty
                ? "藥單 \(Date().formatted(date: .abbreviated, time: .omitted))"
                : prescriptionName.trimmingCharacters(in: .whitespaces)

            for draft in drafts where !draft.drugName.trimmingCharacters(in: .whitespaces).isEmpty {
                let (parsedFreq, parsedMeal) = Self.parseFrequencyAndMeal(draft.frequency)
                let stock = Self.computeStock(totalQuantity: draft.totalQuantity, days: draft.days, frequency: draft.frequency, dosage: draft.dosage)
                let med = Medication(
                    id: UUID().uuidString,
                    profileId: profileId,
                    drugName: draft.drugName,
                    dosage: draft.dosage,
                    frequency: parsedFreq,
                    mealTiming: parsedMeal,
                    nextDoseAt: Date().addingTimeInterval(3600),
                    currentStock: stock,
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
                // 儲存藥單圖片到本地
                if let img = selectedImage {
                    PrescriptionImageStore.save(image: img, forLabel: label)
                }
                showSuccess = true
            } else if let err = lastError {
                phase = .error("新增失敗：\(err)")
            }
        }
    }

    /// 解析 OCR frequency (如「三餐餐後」「每天睡前」「早晚餐後」) → (displayFrequency, mealTiming)
    static func parseFrequencyAndMeal(_ raw: String) -> (String, String) {
        let s = raw.lowercased()
        var freq = "每日 1 次"
        var meal = ""

        // 判斷次數
        if s.contains("三餐") || s.contains("tid") || s.contains("3次") {
            freq = "每日 3 次"
        } else if s.contains("早晚") || s.contains("bid") || s.contains("2次") || s.contains("兩次") {
            freq = "每日 2 次"
        } else if s.contains("四次") || s.contains("qid") || s.contains("4次") {
            freq = "每日 4 次"
        }

        // 判斷用餐時間
        if s.contains("餐後") || s.contains("飯後") {
            meal = "飯後"
        } else if s.contains("餐前") || s.contains("飯前") {
            meal = "飯前"
        } else if s.contains("睡前") {
            meal = "睡前"
            if !s.contains("三餐") && !s.contains("早晚") && !s.contains("四次") {
                freq = "每日 1 次"
            }
        } else if s.contains("空腹") {
            meal = "空腹"
        }

        if meal.isEmpty { meal = "飯後" }
        return (freq, meal)
    }

    /// 從 totalQuantity 或 days*frequency*dose 計算庫存數量
    static func computeStock(totalQuantity: String?, days: Int?, frequency: String, dosage: String) -> Int {
        // 優先從 totalQuantity 解析數字 (e.g. "共 9 TAB" → 9)
        if let tq = totalQuantity {
            let digits = tq.components(separatedBy: CharacterSet.decimalDigits.inverted).joined()
            if let num = Double(digits), num > 0 {
                return Int(ceil(num))
            }
            // 嘗試解析帶小數 (e.g. "共 4.5 TAB")
            let pattern = #"(\d+\.?\d*)"#
            if let range = tq.range(of: pattern, options: .regularExpression),
               let num = Double(tq[range]), num > 0 {
                return Int(ceil(num))
            }
        }

        // fallback: days * timesPerDay * dosePerTime
        let timesPerDay: Int
        let s = frequency.lowercased()
        if s.contains("三餐") || s.contains("tid") || s.contains("3") { timesPerDay = 3 }
        else if s.contains("早晚") || s.contains("bid") || s.contains("2") { timesPerDay = 2 }
        else if s.contains("四") || s.contains("qid") || s.contains("4") { timesPerDay = 4 }
        else { timesPerDay = 1 }

        let dose: Double
        let dosePattern = #"(\d+\.?\d*)"#
        if let range = dosage.range(of: dosePattern, options: .regularExpression),
           let d = Double(dosage[range]) {
            dose = d
        } else {
            dose = 1.0
        }

        let d = days ?? 7
        return Int(ceil(Double(d) * Double(timesPerDay) * dose))
    }
}
