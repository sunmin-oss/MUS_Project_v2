import SwiftUI

/// 空狀態檢視（iOS 16 相容版的 ContentUnavailableView 替代）
struct EmptyStateView: View {
    let titleKey: LocalizedStringKey
    let systemImage: String
    let messageKey: LocalizedStringKey

    var body: some View {
        VStack(spacing: DesignSpacing.md) {
            Image(systemName: systemImage)
                .font(.system(size: 56))
                .foregroundStyle(DesignColors.textSecondary)
            Text(titleKey)
                .font(DesignTypography.title2)
                .foregroundStyle(DesignColors.textPrimary)
            Text(messageKey)
                .font(DesignTypography.body)
                .foregroundStyle(DesignColors.textSecondary)
                .multilineTextAlignment(.center)
        }
        .padding(DesignSpacing.lg)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

#Preview {
    EmptyStateView(titleKey: "medications.empty.title",
                   systemImage: "pills",
                   messageKey: "medications.empty.message")
}
