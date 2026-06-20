import SwiftUI

struct MedicationConfirmView: View {
    let medication: Medication
    @ObservedObject var store: MedicationStore
    let profileId: String
    @EnvironmentObject private var env: AppEnvironment
    @State private var errorMessage: String?
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: DesignSpacing.lg) {
                Spacer()
                Image(systemName: "pills.fill")
                    .font(.system(size: 56))
                    .foregroundStyle(DesignColors.primary)

                VStack(spacing: DesignSpacing.xs) {
                    Text(medication.drugName)
                        .font(DesignTypography.title)
                        .multilineTextAlignment(.center)
                    Text(medication.dosage)
                        .font(DesignTypography.body)
                        .foregroundStyle(DesignColors.textSecondary)
                    Text(medication.nextDoseAt, style: .time)
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                }

                Spacer()

                VStack(spacing: DesignSpacing.sm) {
                    Button {
                        Task {
                            do {
                                try await store.recordTaken(
                                    medicationId: medication.id,
                                    profileId: profileId,
                                    apiClient: env.apiClient)
                                dismiss()
                            } catch { errorMessage = error.localizedDescription }
                        }
                    } label: {
                        SpacedButtonLabel(
                            text: NSLocalizedString("medications.confirm.taken", comment: ""),
                            systemImage: "checkmark.circle.fill")
                    }
                    .buttonStyle(SpacedButtonStyle(filled: true))
                    .accessibilityIdentifier("confirm.taken")

                    Button {
                        dismiss()
                    } label: {
                        SpacedButtonLabel(
                            text: NSLocalizedString("medications.confirm.snooze", comment: ""),
                            systemImage: "alarm")
                    }
                    .buttonStyle(SpacedButtonStyle(filled: false, tint: DesignColors.textPrimary))
                    .accessibilityIdentifier("confirm.snooze")

                    Button {
                        Task {
                            do {
                                try await store.recordSkipped(
                                    medicationId: medication.id,
                                    profileId: profileId,
                                    apiClient: env.apiClient)
                                dismiss()
                            } catch { errorMessage = error.localizedDescription }
                        }
                    } label: {
                        SpacedButtonLabel(
                            text: NSLocalizedString("medications.confirm.skip", comment: ""),
                            systemImage: "xmark.circle")
                    }
                    .buttonStyle(SpacedButtonStyle(filled: false, tint: .red))
                    .accessibilityIdentifier("confirm.skip")
                }
                .padding(.horizontal, DesignSpacing.md)
                .padding(.bottom, DesignSpacing.lg)
            }
            .alert("錯誤", isPresented: .constant(errorMessage != nil),
                   actions: { Button("OK") { errorMessage = nil } },
                   message: { Text(errorMessage ?? "") })
            .navigationTitle("medications.confirm.title")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("general.cancel") { dismiss() }
                }
            }
        }
    }
}
