import SwiftUI

struct MedicationConfirmView: View {
    let medication: Medication
    @ObservedObject var store: MedicationStore
    let profileId: String
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
                            await store.recordTaken(medicationId: medication.id, profileId: profileId)
                            dismiss()
                        }
                    } label: {
                        Label(
                            NSLocalizedString("medications.confirm.taken", comment: ""),
                            systemImage: "checkmark.circle.fill"
                        )
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(DesignColors.primary)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
                    }

                    Button {
                        dismiss()
                        // Re-present after 15 minutes via notification (out of scope here)
                    } label: {
                        Label(
                            NSLocalizedString("medications.confirm.snooze", comment: ""),
                            systemImage: "alarm"
                        )
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(UIColor.secondarySystemBackground))
                        .foregroundStyle(DesignColors.textPrimary)
                        .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
                    }

                    Button(role: .destructive) {
                        Task {
                            await store.recordSkipped(medicationId: medication.id, profileId: profileId)
                            dismiss()
                        }
                    } label: {
                        Label(
                            NSLocalizedString("medications.confirm.skip", comment: ""),
                            systemImage: "xmark.circle"
                        )
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color(UIColor.secondarySystemBackground))
                        .foregroundStyle(.red)
                        .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
                    }
                }
                .padding(.horizontal, DesignSpacing.md)
                .padding(.bottom, DesignSpacing.lg)
            }
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
