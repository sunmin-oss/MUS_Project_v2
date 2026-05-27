import SwiftUI

struct SafetyCheckSheet: View {
    let alerts: [SafetyAlert]
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if alerts.isEmpty {
                    clearView
                } else {
                    alertList
                }

                Spacer()

                Button("safety.check.confirm") { dismiss() }
                    .frame(maxWidth: .infinity, minHeight: 56)
                    .background(DesignColors.primary)
                    .foregroundStyle(.white)
                    .font(DesignTypography.headline)
                    .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
                    .padding(DesignSpacing.md)
            }
            .navigationTitle("safety.check.title")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("general.done") { dismiss() }
                }
            }
        }
    }

    private var clearView: some View {
        VStack(spacing: DesignSpacing.md) {
            Image(systemName: "checkmark.seal.fill")
                .font(.system(size: 64))
                .foregroundStyle(DesignColors.primary)
            Text("safety.check.clear")
                .font(DesignTypography.title2)
                .foregroundStyle(DesignColors.textPrimary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(DesignSpacing.lg)
    }

    private var alertList: some View {
        ScrollView {
            VStack(spacing: DesignSpacing.sm) {
                ForEach(alerts) { alert in
                    SafetyAlertRow(alert: alert)
                }
            }
            .padding(DesignSpacing.md)
        }
    }
}

// MARK: - SafetyAlertRow

private struct SafetyAlertRow: View {
    let alert: SafetyAlert

    var body: some View {
        HStack(alignment: .top, spacing: DesignSpacing.md) {
            Image(systemName: iconName)
                .font(.title2)
                .foregroundStyle(.white)
            VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                HStack {
                    Text(levelLabel)
                        .font(DesignTypography.caption)
                        .padding(.horizontal, DesignSpacing.sm)
                        .padding(.vertical, 2)
                        .background(.white.opacity(0.25))
                        .clipShape(Capsule())
                    Text(alert.title)
                        .font(DesignTypography.headline)
                        .foregroundStyle(.white)
                }
                Text(alert.message)
                    .font(DesignTypography.body)
                    .foregroundStyle(.white.opacity(0.95))
                Text(alert.recommendation)
                    .font(DesignTypography.caption)
                    .foregroundStyle(.white.opacity(0.85))
                    .italic()
            }
            Spacer(minLength: 0)
        }
        .padding(DesignSpacing.md)
        .background(backgroundColor)
        .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
    }

    private var backgroundColor: Color {
        switch alert.level {
        case .contraindicated: return DesignColors.alertCritical
        case .major:           return DesignColors.alertMajor
        case .moderate:        return DesignColors.alertModerate
        case .minor:           return DesignColors.alertMinor
        }
    }

    private var iconName: String {
        switch alert.level {
        case .contraindicated: return "xmark.octagon.fill"
        case .major:           return "exclamationmark.triangle.fill"
        case .moderate:        return "exclamationmark.circle.fill"
        case .minor:           return "info.circle.fill"
        }
    }

    private var levelLabel: String {
        switch alert.level {
        case .contraindicated: return "禁忌"
        case .major:           return "嚴重"
        case .moderate:        return "中度"
        case .minor:           return "輕微"
        }
    }
}

#Preview {
    SafetyCheckSheet(alerts: MockData.safetyAlerts)
}
