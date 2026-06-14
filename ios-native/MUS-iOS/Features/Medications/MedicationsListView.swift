import SwiftUI

struct MedicationsListView: View {
    @EnvironmentObject private var env: AppEnvironment
    @StateObject private var store = MedicationStore()
    @State private var profiles: [Profile] = []
    @State private var isLoading = false
    @State private var showAddSheet = false
    @State private var editingMedication: Medication?
    @State private var confirmingMedication: Medication?

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
                        List {
                            ForEach(filteredMedications) { med in
                                medicationRow(med)
                                    .listRowInsets(EdgeInsets(top: 6, leading: 16, bottom: 6, trailing: 16))
                            }
                            .onDelete { offsets in
                                deleteMedications(at: offsets)
                            }
                        }
                        .listStyle(.plain)
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
                    NavigationLink {
                        MedicationCalendarView(store: store)
                    } label: {
                        Image(systemName: "calendar.badge.checkmark")
                    }
                }
            }
            .task(id: env.selectedProfileId) {
                await loadAll()
            }
            .sheet(isPresented: $showAddSheet) {
                AddMedicationView(store: store, editingMedication: editingMedication)
            }
            .sheet(item: $confirmingMedication) { med in
                MedicationConfirmView(medication: med, store: store, profileId: env.selectedProfileId)
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
                    stockBadge(med.currentStock)
                }
                Text("\(med.dosage) ・ \(med.frequency) ・ \(med.mealTiming)")
                    .font(DesignTypography.body)
                    .foregroundStyle(DesignColors.textSecondary)
                HStack {
                    Image(systemName: "clock")
                        .font(.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                    Text(med.nextDoseAt, style: .relative)
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                    Spacer()
                    Button {
                        confirmingMedication = med
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
}

#Preview {
    MedicationsListView().environmentObject(AppEnvironment.makeDefault())
}

