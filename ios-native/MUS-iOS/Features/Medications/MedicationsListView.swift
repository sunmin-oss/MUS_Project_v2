import SwiftUI

struct MedicationsListView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var store: MedicationStore
    @State private var profiles: [Profile] = []
    @State private var isLoading = false
    @State private var showAddSheet = false
    @State private var editingMedication: Medication?
    @State private var confirmingMedication: Medication?
    @State private var overdoseMedication: Medication?
    @State private var showOverdoseAlert = false
    @State private var isEditMode = false
    @State private var selectedIds: Set<String> = []
    @State private var showDeleteConfirm = false

    private var filteredMedications: [Medication] {
        store.medications.filter { $0.profileId == env.selectedProfileId }
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if !profiles.isEmpty {
                    ProfileSwitcherView(profiles: profiles)
                        .padding(.top, DesignSpacing.xs)
                }

                Group {
                    if isLoading {
                        ProgressView().controlSize(.large)
                            .frame(maxWidth: .infinity, maxHeight: .infinity)
                    } else if filteredMedications.isEmpty {
                        EmptyStateView(
                            titleKey: "medications.empty.title",
                            systemImage: "pills",
                            messageKey: "medications.empty.message"
                        )
                    } else {
                        VStack(spacing: 0) {
                            if isEditMode {
                                HStack {
                                    Button {
                                        if selectedIds.count == filteredMedications.count {
                                            selectedIds.removeAll()
                                        } else {
                                            selectedIds = Set(filteredMedications.map(\.id))
                                        }
                                    } label: {
                                        Text(selectedIds.count == filteredMedications.count ? "取消全選" : "全選")
                                            .font(DesignTypography.caption)
                                    }
                                    Spacer()
                                    if !selectedIds.isEmpty {
                                        Text("已選擇 \(selectedIds.count) 項")
                                            .font(DesignTypography.caption)
                                            .foregroundStyle(DesignColors.textSecondary)
                                    }
                                    Spacer()
                                    Button(role: .destructive) {
                                        showDeleteConfirm = true
                                    } label: {
                                        Label("刪除", systemImage: "trash")
                                            .font(DesignTypography.caption)
                                    }
                                    .disabled(selectedIds.isEmpty)
                                }
                                .padding(.horizontal, DesignSpacing.md)
                                .padding(.vertical, DesignSpacing.sm)
                                .background(Color(UIColor.secondarySystemBackground))
                            }
                            List(selection: isEditMode ? $selectedIds : nil) {
                                ForEach(filteredMedications) { med in
                                    medicationRow(med)
                                        .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                                        .tag(med.id)
                                }
                                .onDelete { offsets in
                                    deleteMedications(at: offsets)
                                }
                            }
                            .listStyle(.plain)
                            .environment(\.editMode, isEditMode ? .constant(.active) : .constant(.inactive))
                        }
                    }
                }
            }
            .background(DesignColors.background)
            .navigationTitle("tab.medications")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        editingMedication = nil
                        showAddSheet = true
                    } label: {
                        Label("medications.add.title", systemImage: "plus")
                    }
                }
                ToolbarItem(placement: .navigationBarLeading) {
                    HStack(spacing: 12) {
                        NavigationLink {
                            MedicationCalendarView(store: store)
                        } label: {
                            Image(systemName: "calendar.badge.checkmark")
                        }
                        if !filteredMedications.isEmpty {
                            Button {
                                withAnimation {
                                    isEditMode.toggle()
                                    if !isEditMode { selectedIds.removeAll() }
                                }
                            } label: {
                                Text(isEditMode ? "完成" : "編輯")
                            }
                        }
                    }
                }
            }
            .task(id: env.selectedProfileId) {
                await loadAll()
            }
            .onAppear {
                Task { await loadAll() }
            }
            .sheet(isPresented: $showAddSheet, onDismiss: {
                Task { await loadAll() }
            }) {
                AddMedicationView(store: store, editingMedication: editingMedication)
            }
            .refreshable { await loadAll() }
            .sheet(item: $confirmingMedication, onDismiss: {
                Task { await loadAll() }
            }) { med in
                MedicationConfirmView(medication: med, store: store, profileId: env.selectedProfileId)
            }
            .alert("用藥提醒", isPresented: $showOverdoseAlert, presenting: overdoseMedication) { med in
                Button("仍要服藥", role: .destructive) {
                    confirmingMedication = med
                    overdoseMedication = nil
                }
                Button("取消", role: .cancel) {
                    overdoseMedication = nil
                }
            } message: { med in
                Text(med.drugName + " 今日已服用 " + String(todayTakenCount(for: med.id)) + " 次，已達規定的 " + String(dailyLimit(for: med)) + " 次。確定要繼續服用嗎？")
            }
            .alert("確認刪除", isPresented: $showDeleteConfirm) {
                Button("刪除 \(selectedIds.count) 項藥物", role: .destructive) {
                    batchDelete()
                }
                Button("取消", role: .cancel) {}
            } message: {
                Text("刪除後無法恢復，確定要刪除已選擇的藥物嗎？")
            }
        }
    }

    @ViewBuilder
    private func medicationRow(_ med: Medication) -> some View {
        Card {
            VStack(alignment: .leading, spacing: DesignSpacing.sm) {
                HStack {
                    Text(med.drugName)
                        .font(DesignTypography.title2)
                    Spacer()
                    todayBadge(todayTakenCount(for: med.id))
                    stockBadge(med.currentStock)
                }
                Text("\(med.dosage) ・ \(med.frequency) ・ \(med.mealTiming)")
                    .font(DesignTypography.body)
                    .foregroundStyle(DesignColors.textSecondary)
                HStack {
                    Image(systemName: "clock")
                        .font(.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                    Text("下次服藥：" + med.nextDoseAt.formatted(date: .omitted, time: .shortened))
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                    Spacer()
                    Button {
                        let taken = todayTakenCount(for: med.id)
                        let limit = dailyLimit(for: med)
                        if taken >= limit {
                            overdoseMedication = med
                            showOverdoseAlert = true
                        } else {
                            confirmingMedication = med
                        }
                    } label: {
                        Label("確認服藥", systemImage: "checkmark.circle.fill")
                            .font(DesignTypography.caption)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 5)
                            .background(DesignColors.primary.opacity(0.12))
                            .foregroundStyle(DesignColors.primary)
                            .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .onTapGesture {
            editingMedication = med
            showAddSheet = true
        }
    }

    @ViewBuilder
    private func stockBadge(_ count: Int) -> some View {
        let isLow = count <= 7
        Text(String(format: NSLocalizedString("medications.stock", comment: ""), count))
            .font(DesignTypography.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(isLow ? Color.red.opacity(0.12) : Color(UIColor.secondarySystemBackground))
            .foregroundStyle(isLow ? .red : DesignColors.textSecondary)
            .clipShape(Capsule())
    }


    private func dailyLimit(for med: Medication) -> Int {
        if let match = med.frequency.range(of: "[0-9]+", options: .regularExpression) {
            return Int(med.frequency[match]) ?? 1
        }
        return 1
    }

    private func todayTakenCount(for medicationId: String) -> Int {
        let start = Calendar.current.startOfDay(for: Date())
        return store.records.filter {
            $0.medicationId == medicationId
            && $0.status == .taken
            && $0.scheduledAt >= start
        }.count
    }

    @ViewBuilder
    private func todayBadge(_ count: Int) -> some View {
        let label = String(format: NSLocalizedString("medications.today.taken", comment: ""), count)
        Text(label)
            .font(DesignTypography.caption)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(count > 0 ? DesignColors.primary.opacity(0.12) : Color(UIColor.secondarySystemBackground))
            .foregroundStyle(count > 0 ? DesignColors.primary : DesignColors.textSecondary)
            .clipShape(Capsule())
    }

    private func loadAll() async {
        isLoading = true
        defer { isLoading = false }
        do {
            profiles = try await env.apiClient.fetchProfiles()
            await store.load(profileId: env.selectedProfileId, apiClient: env.apiClient)
        } catch {
            // silently ignore — store keeps its previous state
        }
    }

    private func deleteMedications(at offsets: IndexSet) {
        let idsToDelete = offsets.map { filteredMedications[$0].id }
        Task {
            for id in idsToDelete {
                try? await store.delete(id: id, apiClient: env.apiClient)
            }
        }
    }

    private func batchDelete() {
        let ids = selectedIds
        Task {
            for id in ids {
                try? await store.delete(id: id, apiClient: env.apiClient)
            }
            selectedIds.removeAll()
            isEditMode = false
            await loadAll()
        }
    }
}

#Preview {
    let env = AppEnvironment.makeDefault()
    return MedicationsListView()
        .environmentObject(env)
        .environmentObject(env.medicationStore)
}

