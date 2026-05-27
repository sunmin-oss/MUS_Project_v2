import SwiftUI

/// Add or edit a single Medication
struct AddMedicationView: View {
    @EnvironmentObject private var env: AppEnvironment
    @ObservedObject var store: MedicationStore
    var editingMedication: Medication? = nil
    @Environment(\.dismiss) private var dismiss

    @State private var drugName = ""
    @State private var dosage = ""
    @State private var frequency = "每日一次"
    @State private var mealTiming = "飯後"
    @State private var currentStock = 10
    @State private var notes = ""
    @State private var reminderTimes: [Date] = []
    @State private var isSaving = false
    @State private var errorMessage: String?
    @State private var safetyAlerts: [SafetyAlert] = []
    @State private var showSafetyCheck = false

    private let frequencyOptions = ["每日一次", "每日兩次", "三餐飯後", "每 6 小時", "需要時"]
    private let mealTimingOptions = ["飯前", "飯後", "隨時"]

    var isEditing: Bool { editingMedication != nil }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    TextField(
                        NSLocalizedString("medications.drug.name", comment: ""),
                        text: $drugName
                    )
                    TextField(
                        NSLocalizedString("medications.dosage", comment: ""),
                        text: $dosage
                    )
                }

                Section {
                    Picker(NSLocalizedString("medications.frequency", comment: ""), selection: $frequency) {
                        ForEach(frequencyOptions, id: \.self) { Text($0).tag($0) }
                    }
                    Picker(NSLocalizedString("medications.meal.timing", comment: ""), selection: $mealTiming) {
                        ForEach(mealTimingOptions, id: \.self) { Text($0).tag($0) }
                    }
                }

                Section {
                    Stepper(
                        String(format: NSLocalizedString("medications.stock", comment: ""), currentStock),
                        value: $currentStock, in: 0...999
                    )
                } header: {
                    Text("medications.stock.low")
                }

                Section {
                    ForEach(reminderTimes.indices, id: \.self) { idx in
                        DatePicker(
                            "時間 \(idx + 1)",
                            selection: Binding(
                                get: { reminderTimes[idx] },
                                set: { reminderTimes[idx] = $0 }
                            ),
                            displayedComponents: .hourAndMinute
                        )
                    }
                    if reminderTimes.count < 3 {
                        Button {
                            reminderTimes.append(Calendar.current.startOfDay(for: Date()).addingTimeInterval(8 * 3600))
                        } label: {
                            Label("新增提醒時間", systemImage: "plus")
                        }
                    }
                    if !reminderTimes.isEmpty {
                        Button(role: .destructive) {
                            reminderTimes.removeLast()
                        } label: {
                            Label("移除最後一個時間", systemImage: "minus")
                        }
                    }
                } header: {
                    Text("medications.reminder.times")
                }

                Section {
                    TextField(
                        NSLocalizedString("medications.notes", comment: ""),
                        text: $notes,
                        axis: .vertical
                    )
                    .lineLimit(3...6)
                } header: {
                    Text("medications.notes")
                }

                if let error = errorMessage {
                    Section {
                        Text(error).foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle(isEditing ? "medications.edit.title" : "medications.add.title")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("general.cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("general.save") { save() }
                        .disabled(drugName.trimmingCharacters(in: .whitespaces).isEmpty || isSaving)
                }
            }
            .onAppear { prefill() }
            .sheet(isPresented: $showSafetyCheck) {
                SafetyCheckSheet(alerts: safetyAlerts)
            }
        }
    }

    private func prefill() {
        guard let med = editingMedication else { return }
        drugName = med.drugName
        dosage = med.dosage
        frequency = med.frequency
        mealTiming = med.mealTiming
        currentStock = med.currentStock
        notes = med.notes
        reminderTimes = med.reminderTimes
    }

    private func save() {
        isSaving = true
        let profileId = env.selectedProfileId
        let med = Medication(
            id: editingMedication?.id ?? UUID().uuidString,
            profileId: profileId,
            drugName: drugName.trimmingCharacters(in: .whitespaces),
            dosage: dosage.trimmingCharacters(in: .whitespaces),
            frequency: frequency,
            mealTiming: mealTiming,
            nextDoseAt: Date().addingTimeInterval(3600),
            currentStock: currentStock,
            reminderTimes: reminderTimes,
            notes: notes
        )
        Task {
            do {
                if isEditing {
                    try await store.update(medication: med, apiClient: env.apiClient)
                } else {
                    try await store.add(medication: med, apiClient: env.apiClient)
                }
                // Trigger safety check after save
                let alerts = try await env.apiClient.checkSafety(profileId: profileId, drugIds: [0])
                isSaving = false
                if alerts.isEmpty {
                    dismiss()
                } else {
                    safetyAlerts = alerts
                    showSafetyCheck = true
                }
            } catch {
                errorMessage = error.localizedDescription
                isSaving = false
            }
        }
    }
}
