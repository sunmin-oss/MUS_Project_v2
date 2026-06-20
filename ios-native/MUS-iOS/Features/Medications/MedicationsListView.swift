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
    @State private var showDeletePrescriptionConfirm = false
    @State private var prescriptionToDelete: String? = nil
    @State private var selectedTab: MedTab = .all
    @State private var selectedPrescription: String? = nil
    @State private var showPrescriptionImages = false
    @State private var drugNameCache: [String: String] = [:]  // medId -> chineseName

    enum MedTab: String, CaseIterable {
        case all = "全部"
        case morning = "早上"
        case noon = "中午"
        case evening = "晚上"
        case bedtime = "睡前"
    }

    /// 所有不重複的藥單標籤
    private var prescriptionLabels: [String] {
        let profileMeds = store.medications.filter { $0.profileId == env.selectedProfileId }
        var labels: [String] = []
        let named = profileMeds.compactMap(\.prescriptionLabel).filter { !$0.isEmpty }
        labels = Array(Set(named)).sorted()
        // 若有未分類的藥物，加入「未分類」
        if profileMeds.contains(where: { ($0.prescriptionLabel ?? "").isEmpty }) {
            labels.insert("未分類", at: 0)
        }
        return labels
    }

    private var filteredMedications: [Medication] {
        var meds = store.medications.filter { $0.profileId == env.selectedProfileId }

        // 藥單篩選
        if let prescription = selectedPrescription {
            if prescription == "未分類" {
                meds = meds.filter { ($0.prescriptionLabel ?? "").isEmpty }
            } else {
                meds = meds.filter { $0.prescriptionLabel == prescription }
            }
        }

        // 時段篩選
        switch selectedTab {
        case .all:
            return meds
        case .morning:
            return meds.filter { isMorning($0) }
        case .noon:
            return meds.filter { isNoon($0) }
        case .evening:
            return meds.filter { isEvening($0) }
        case .bedtime:
            return meds.filter { isBedtime($0) }
        }
    }

    private func isMorning(_ med: Medication) -> Bool {
        let text = med.frequency + med.mealTiming
        return text.contains("早") || text.contains("morning")
    }
    private func isNoon(_ med: Medication) -> Bool {
        let text = med.frequency + med.mealTiming
        return text.contains("午") || text.contains("中") || text.contains("noon") || text.contains("三餐")
    }
    private func isEvening(_ med: Medication) -> Bool {
        let text = med.frequency + med.mealTiming
        return text.contains("晚") || text.contains("evening") || text.contains("三餐")
    }
    private func isBedtime(_ med: Medication) -> Bool {
        let text = med.frequency + med.mealTiming
        return text.contains("睡前") || text.contains("bedtime")
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if !profiles.isEmpty {
                    ProfileSwitcherView(profiles: profiles)
                        .padding(.top, DesignSpacing.xs)
                }

                // 藥單選擇器
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        prescriptionChip(nil, label: "所有藥單")
                        ForEach(prescriptionLabels, id: \.self) { label in
                            prescriptionChip(label, label: label)
                                .contextMenu {
                                    if label != "未分類" {
                                        Button(role: .destructive) {
                                            prescriptionToDelete = label
                                            showDeletePrescriptionConfirm = true
                                        } label: {
                                            Label("刪除整張藥單", systemImage: "trash")
                                        }
                                    }
                                }
                        }
                    }
                    .padding(.horizontal, DesignSpacing.md)
                    .padding(.vertical, DesignSpacing.xs)
                }

                // 時段分頁標籤
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        ForEach(MedTab.allCases, id: \.self) { tab in
                            tabButton(tab)
                        }
                    }
                    .padding(.horizontal, DesignSpacing.md)
                    .padding(.vertical, DesignSpacing.sm)
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
                        Button {
                            showPrescriptionImages = true
                        } label: {
                            Image(systemName: "doc.text.image")
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
            .refreshable {
                drugNameCache.removeAll()
                await loadAll()
            }
            .sheet(isPresented: $showPrescriptionImages, onDismiss: {
                Task { await loadAll() }
            }) {
                NavigationStack {
                    PrescriptionImagesView()
                }
                .environmentObject(env)
                .environmentObject(store)
            }
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
            .alert("刪除整張藥單", isPresented: $showDeletePrescriptionConfirm) {
                Button("刪除", role: .destructive) {
                    deletePrescription()
                }
                Button("取消", role: .cancel) {
                    prescriptionToDelete = nil
                }
            } message: {
                if let name = prescriptionToDelete {
                    Text("將刪除「\(name)」藥單中的所有藥物，此操作無法恢復。")
                }
            }
        }
    }

    @ViewBuilder
    private func prescriptionChip(_ value: String?, label: String) -> some View {
        let isSelected = selectedPrescription == value
        HStack(spacing: 0) {
            Button {
                withAnimation(.easeInOut(duration: 0.2)) { selectedPrescription = value }
            } label: {
                HStack(spacing: 4) {
                    Image(systemName: value == nil ? "list.bullet" : "doc.text")
                        .font(.system(size: 12))
                    Text(label)
                }
                .font(.system(size: 13, weight: isSelected ? .bold : .medium))
                .padding(.leading, 12)
                .padding(.trailing, isEditMode && value != nil && value != "未分類" ? 4 : 12)
                .padding(.vertical, 6)
                .foregroundStyle(isSelected ? .white : DesignColors.primary)
            }
            .buttonStyle(.plain)

            if isEditMode, let val = value, val != "未分類" {
                Button {
                    prescriptionToDelete = val
                    showDeletePrescriptionConfirm = true
                } label: {
                    Image(systemName: "trash")
                        .font(.system(size: 11))
                        .foregroundStyle(isSelected ? .white.opacity(0.9) : .red)
                        .padding(.trailing, 10)
                        .padding(.vertical, 6)
                }
                .buttonStyle(.plain)
            }
        }
        .background(
            Capsule().fill(isSelected ? DesignColors.primary.opacity(0.8) : DesignColors.primary.opacity(0.1))
        )
    }

    @ViewBuilder
    private func tabButton(_ tab: MedTab) -> some View {
        let isSelected = selectedTab == tab
        let count = tabCount(tab)
        Button {
            withAnimation(.easeInOut(duration: 0.2)) { selectedTab = tab }
        } label: {
            HStack(spacing: 4) {
                Text(tab.rawValue)
                if count > 0 && tab != .all {
                    Text("\(count)")
                        .font(.system(size: 11, weight: .semibold))
                        .foregroundStyle(isSelected ? .white : DesignColors.primary)
                        .padding(.horizontal, 5)
                        .padding(.vertical, 1)
                        .background(
                            Capsule().fill(isSelected ? Color.white.opacity(0.3) : DesignColors.primary.opacity(0.15))
                        )
                }
            }
            .font(.system(size: 14, weight: isSelected ? .bold : .medium))
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .foregroundStyle(isSelected ? .white : DesignColors.textSecondary)
            .background(
                Capsule().fill(isSelected ? DesignColors.primary : Color(UIColor.secondarySystemBackground))
            )
        }
        .buttonStyle(.plain)
    }

    private func tabCount(_ tab: MedTab) -> Int {
        let profileMeds = store.medications.filter { $0.profileId == env.selectedProfileId }
        switch tab {
        case .all: return profileMeds.count
        case .morning: return profileMeds.filter { isMorning($0) }.count
        case .noon: return profileMeds.filter { isNoon($0) }.count
        case .evening: return profileMeds.filter { isEvening($0) }.count
        case .bedtime: return profileMeds.filter { isBedtime($0) }.count
        }
    }

    @ViewBuilder
    private func medicationRow(_ med: Medication) -> some View {
        NavigationLink {
            MedicationDetailView(store: store, medication: med)
        } label: {
            Card {
                VStack(alignment: .leading, spacing: DesignSpacing.sm) {
                    HStack {
                        Text(drugNameCache[med.id] ?? med.drugName)
                            .font(DesignTypography.title2)
                        Spacer()
                        todayBadge(todayTakenCount(for: med.id))
                        stockBadge(med)
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
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func stockBadge(_ med: Medication) -> some View {
        let isLow = med.isStockLow
        Text(String(format: NSLocalizedString("medications.stock", comment: ""), med.currentStock.stockDisplay))
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
        // 先載入快取的 profiles
        if profiles.isEmpty, let cached = LocalCache.load([Profile].self, forKey: "profiles") {
            profiles = cached
        }
        do {
            profiles = try await env.apiClient.fetchProfiles()
            LocalCache.save(profiles, forKey: "profiles")
            await store.load(profileId: env.selectedProfileId, apiClient: env.apiClient)
        } catch {
            // 失敗時保留快取資料
            await store.load(profileId: env.selectedProfileId, apiClient: env.apiClient)
        }
        // 批次查詢中文名
        await loadChineseNames()
    }

    private func loadChineseNames() async {
        let meds = store.medications.filter { $0.profileId == env.selectedProfileId }
        for med in meds {
            let queries = MedicationDetailView.searchQueries(for: med.drugName)
            for query in queries {
                if let results = try? await env.apiClient.searchDrugs(query: query, limit: 1),
                   let first = results.first,
                   !first.chineseName.isEmpty {
                    drugNameCache[med.id] = first.chineseName
                    break
                }
            }
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
        // 找出即將被刪除的藥物所屬的藥單標籤
        let deletingMeds = store.medications.filter { ids.contains($0.id) }
        let affectedLabels = Set(deletingMeds.compactMap(\.prescriptionLabel).filter { !$0.isEmpty })

        Task {
            for id in ids {
                try? await store.delete(id: id, apiClient: env.apiClient)
            }
            // 檢查每個受影響的藥單：如果該藥單下所有藥物都被刪除了，同步刪除圖片
            for label in affectedLabels {
                let remaining = store.medications.filter {
                    $0.profileId == env.selectedProfileId && $0.prescriptionLabel == label
                }
                if remaining.isEmpty {
                    PrescriptionImageStore.remove(forLabel: label)
                }
            }
            selectedIds.removeAll()
            isEditMode = false
            await loadAll()
        }
    }

    private func deletePrescription() {
        guard let label = prescriptionToDelete else { return }
        let medsToDelete = store.medications.filter { med in
            med.profileId == env.selectedProfileId &&
            (label == "未分類" ? (med.prescriptionLabel ?? "").isEmpty : med.prescriptionLabel == label)
        }
        Task {
            for med in medsToDelete {
                try? await store.delete(id: med.id, apiClient: env.apiClient)
            }
            // 同步刪除本地藥單圖片
            if label != "未分類" {
                PrescriptionImageStore.remove(forLabel: label)
            }
            // 如果刪的是目前選取的藥單，重置為所有藥單
            if selectedPrescription == label {
                selectedPrescription = nil
            }
            prescriptionToDelete = nil
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

