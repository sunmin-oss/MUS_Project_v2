import SwiftUI

struct MedicationsListView: View {
    @EnvironmentObject private var env: AppEnvironment
    @State private var medications: [Medication] = []
    @State private var isLoading = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            Group {
                if isLoading {
                    ProgressView().controlSize(.large)
                } else if medications.isEmpty {
                    EmptyStateView(titleKey: "medications.empty.title",
                                   systemImage: "pills",
                                   messageKey: "medications.empty.message")
                } else {
                    ScrollView {
                        LazyVStack(spacing: DesignSpacing.md) {
                            ForEach(medications) { med in
                                Card {
                                    VStack(alignment: .leading, spacing: DesignSpacing.sm) {
                                        Text(med.drugName).font(DesignTypography.title2)
                                        Text("\(med.dosage) ・ \(med.frequency)")
                                            .font(DesignTypography.body)
                                            .foregroundStyle(DesignColors.textSecondary)
                                        Text(String(format: NSLocalizedString("medications.stock", comment: ""), med.currentStock))
                                            .font(DesignTypography.caption)
                                            .foregroundStyle(med.currentStock < 5 ? DesignColors.alertMajor : DesignColors.textSecondary)
                                    }
                                }
                            }
                        }
                        .padding(DesignSpacing.md)
                    }
                }
            }
            .background(DesignColors.background)
            .navigationTitle("tab.medications")
            .task { await load() }
        }
    }

    private func load() async {
        isLoading = true
        defer { isLoading = false }
        do {
            medications = try await env.apiClient.fetchMedications(profileId: "p1")
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

#Preview {
    MedicationsListView().environmentObject(AppEnvironment.makeDefault())
}
