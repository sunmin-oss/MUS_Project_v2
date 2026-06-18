import SwiftUI

/// 個人基本資訊編輯頁面（身高、體重、年齡、性別、血型）
struct PersonalInfoView: View {
    @EnvironmentObject private var env: AppEnvironment

    @State private var height: String = ""        // cm
    @State private var weight: String = ""        // kg
    @State private var birthDate: Date = Calendar.current.date(from: DateComponents(year: 1990, month: 1, day: 1))!
    @State private var hasBirthDate: Bool = false
    @State private var gender: Gender = .unspecified
    @State private var bloodType: BloodType = .unknown
    @State private var showSaved = false
    @State private var showValidationError = false
    @State private var validationError: String = ""

    enum Gender: String, CaseIterable, Identifiable {
        case male = "male"
        case female = "female"
        case other = "other"
        case unspecified = "unspecified"
        var id: String { rawValue }
        var label: String {
            switch self {
            case .male: return "男"
            case .female: return "女"
            case .other: return "其他"
            case .unspecified: return "未設定"
            }
        }
    }

    enum BloodType: String, CaseIterable, Identifiable {
        case a = "A"
        case b = "B"
        case ab = "AB"
        case o = "O"
        case unknown = "unknown"
        var id: String { rawValue }
        var label: String {
            switch self {
            case .unknown: return "未設定"
            default: return rawValue + " 型"
            }
        }
    }

    private let store = PersonalInfoStore.shared

    var body: some View {
        formContent
            .navigationTitle("個人資訊")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("儲存") { save() }
                        .font(.system(size: 16, weight: .semibold))
                }
            }
            .onAppear { load() }
            .alert("輸入錯誤", isPresented: $showValidationError) {
                Button("確定", role: .cancel) {}
            } message: {
                Text(validationError)
            }
            .overlay {
                if showSaved {
                    savedToast
                }
            }
    }

    private var formContent: some View {
        Form {
            Section {
                HStack {
                    Image(systemName: "person.crop.circle.fill")
                        .font(.system(size: 48))
                        .foregroundStyle(DesignColors.primary)
                    VStack(alignment: .leading, spacing: 4) {
                        Text(env.currentUsername ?? "使用者")
                            .font(.system(size: 18, weight: .semibold))
                        Text("管理您的個人健康資訊")
                            .font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                    .padding(.leading, 8)
                }
                .padding(.vertical, 4)
            }

            Section("基本資料") {
                HStack {
                    Label("身高", systemImage: "ruler")
                        .font(DesignTypography.body)
                    Spacer()
                    TextField("cm", text: $height)
                        .keyboardType(.decimalPad)
                        .multilineTextAlignment(.trailing)
                        .frame(width: 80)
                        .onChange(of: height) { newValue in
                            let filtered = newValue.filter { $0.isNumber || $0 == "." }
                            if filtered != newValue { height = filtered }
                        }
                    Text("cm")
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                }

                HStack {
                    Label("體重", systemImage: "scalemass")
                        .font(DesignTypography.body)
                    Spacer()
                    TextField("kg", text: $weight)
                        .keyboardType(.decimalPad)
                        .multilineTextAlignment(.trailing)
                        .frame(width: 80)
                        .onChange(of: weight) { newValue in
                            let filtered = newValue.filter { $0.isNumber || $0 == "." }
                            if filtered != newValue { weight = filtered }
                        }
                    Text("kg")
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                }

                DatePicker(
                    selection: $birthDate,
                    in: ...Date.now,
                    displayedComponents: .date
                ) {
                    Label("出生日期", systemImage: "calendar")
                        .font(DesignTypography.body)
                }
                .onChange(of: birthDate) { _ in hasBirthDate = true }

                Picker(selection: $gender) {
                    ForEach(Gender.allCases) { g in
                        Text(g.label).tag(g)
                    }
                } label: {
                    Label("性別", systemImage: "person.fill")
                        .font(DesignTypography.body)
                }
                .pickerStyle(.menu)

                Picker(selection: $bloodType) {
                    ForEach(BloodType.allCases) { bt in
                        Text(bt.label).tag(bt)
                    }
                } label: {
                    Label("血型", systemImage: "drop.fill")
                        .font(DesignTypography.body)
                }
                .pickerStyle(.menu)
            }

            if let bmi = computedBMI {
                Section("健康指標") {
                    HStack {
                        Label("BMI", systemImage: "heart.text.square")
                            .font(DesignTypography.body)
                        Spacer()
                        Text(String(format: "%.1f", bmi))
                            .font(.system(size: 17, weight: .medium))
                            .foregroundStyle(bmiColor(bmi))
                        Text(bmiCategory(bmi))
                            .font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                }
            }

            Section {
                HStack(alignment: .top, spacing: DesignSpacing.sm) {
                    Image(systemName: "lock.shield")
                        .foregroundStyle(DesignColors.primary)
                    Text("您的個人資訊僅儲存在本機裝置上，不會上傳至伺服器。")
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                }
            }
        }
    }

    // MARK: - BMI

    private var computedBMI: Double? {
        guard let h = Double(height), h > 0,
              let w = Double(weight), w > 0 else { return nil }
        let heightInM = h / 100.0
        return w / (heightInM * heightInM)
    }

    private func bmiColor(_ bmi: Double) -> Color {
        switch bmi {
        case ..<18.5: return .blue
        case 18.5..<24: return .green
        case 24..<27: return .orange
        default: return .red
        }
    }

    private func bmiCategory(_ bmi: Double) -> String {
        switch bmi {
        case ..<18.5: return "過輕"
        case 18.5..<24: return "正常"
        case 24..<27: return "過重"
        default: return "肥胖"
        }
    }

    // MARK: - Toast

    private var savedToast: some View {
        VStack {
            Spacer()
            Text("✓ 已儲存")
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(.white)
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
                .background(Capsule().fill(Color.green))
                .padding(.bottom, 40)
        }
        .transition(.move(edge: .bottom).combined(with: .opacity))
        .animation(.easeInOut, value: showSaved)
    }

    // MARK: - Persistence

    private func save() {
        if !height.isEmpty {
            guard let h = Double(height), h >= 50, h <= 250 else {
                validationError = "身高請輸入 50~250 cm"; showValidationError = true; return
            }
        }
        if !weight.isEmpty {
            guard let w = Double(weight), w >= 20, w <= 300 else {
                validationError = "體重請輸入 20~300 kg"; showValidationError = true; return
            }
        }
        store.height = Double(height)
        store.weight = Double(weight)
        store.birthDate = hasBirthDate ? birthDate : nil
        store.gender = gender.rawValue
        store.bloodType = bloodType.rawValue
        store.save()

        withAnimation { showSaved = true }
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
            withAnimation { showSaved = false }
        }
    }

    private func load() {
        store.load()
        if let h = store.height { height = String(format: "%.0f", h) }
        if let w = store.weight { weight = String(format: "%.1f", w) }
        if let d = store.birthDate { birthDate = d; hasBirthDate = true }
        gender = Gender(rawValue: store.gender ?? "unspecified") ?? .unspecified
        bloodType = BloodType(rawValue: store.bloodType ?? "unknown") ?? .unknown
    }
}

// MARK: - PersonalInfoStore

/// 本地個人資訊儲存（UserDefaults）
final class PersonalInfoStore {
    static let shared = PersonalInfoStore()

    private let prefix = "personalInfo."
    private var defaults: UserDefaults { .standard }

    var height: Double?
    var weight: Double?
    var birthDate: Date?
    var gender: String?
    var bloodType: String?

    func save() {
        setOrRemove(height, key: "height")
        setOrRemove(weight, key: "weight")
        if let d = birthDate {
            defaults.set(d.timeIntervalSince1970, forKey: prefix + "birthDate")
        } else {
            defaults.removeObject(forKey: prefix + "birthDate")
        }
        defaults.set(gender, forKey: prefix + "gender")
        defaults.set(bloodType, forKey: prefix + "bloodType")
    }

    func load() {
        height = doubleOrNil("height")
        weight = doubleOrNil("weight")
        let ts = defaults.double(forKey: prefix + "birthDate")
        birthDate = ts == 0 ? nil : Date(timeIntervalSince1970: ts)
        gender = defaults.string(forKey: prefix + "gender")
        bloodType = defaults.string(forKey: prefix + "bloodType")
    }

    private func setOrRemove(_ val: Double?, key: String) {
        if let v = val { defaults.set(v, forKey: prefix + key) }
        else { defaults.removeObject(forKey: prefix + key) }
    }

    private func doubleOrNil(_ key: String) -> Double? {
        let v = defaults.double(forKey: prefix + key)
        return v == 0 ? nil : v
    }
}

#Preview {
    NavigationStack {
        PersonalInfoView()
            .environmentObject(AppEnvironment.makeDefault())
    }
}
