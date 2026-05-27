import SwiftUI

/// 安全警示橫幅（對應 Spec 06 的四級警示）
struct AlertBanner: View {
    enum Level { case critical, major, moderate, minor }

    let level: Level
    let titleKey: LocalizedStringKey
    let messageKey: LocalizedStringKey

    var body: some View {
        HStack(alignment: .top, spacing: DesignSpacing.md) {
            Image(systemName: iconName)
                .font(.title2)
                .foregroundStyle(.white)
            VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                Text(titleKey)
                    .font(DesignTypography.headline)
                    .foregroundStyle(.white)
                Text(messageKey)
                    .font(DesignTypography.body)
                    .foregroundStyle(.white.opacity(0.95))
            }
            Spacer(minLength: 0)
        }
        .padding(DesignSpacing.md)
        .background(backgroundColor)
        .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
    }

    private var backgroundColor: Color {
        switch level {
        case .critical: return DesignColors.alertCritical
        case .major:    return DesignColors.alertMajor
        case .moderate: return DesignColors.alertModerate
        case .minor:    return DesignColors.alertMinor
        }
    }

    private var iconName: String {
        switch level {
        case .critical: return "xmark.octagon.fill"
        case .major:    return "exclamationmark.triangle.fill"
        case .moderate: return "exclamationmark.circle.fill"
        case .minor:    return "info.circle.fill"
        }
    }
}

#Preview {
    VStack(spacing: 12) {
        AlertBanner(level: .critical, titleKey: "alert.contraindicated.title", messageKey: "alert.contraindicated.message")
        AlertBanner(level: .major, titleKey: "alert.major.title", messageKey: "alert.major.message")
        AlertBanner(level: .moderate, titleKey: "alert.moderate.title", messageKey: "alert.moderate.message")
        AlertBanner(level: .minor, titleKey: "alert.minor.title", messageKey: "alert.minor.message")
    }
    .padding()
}
