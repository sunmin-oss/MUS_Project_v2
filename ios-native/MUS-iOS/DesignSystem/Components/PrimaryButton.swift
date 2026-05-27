import SwiftUI

/// 主要操作按鈕（CTA）。最小高度 56pt，符合長者觸控需求。
struct PrimaryButton: View {
    let titleKey: LocalizedStringKey
    let systemImage: String?
    let action: () -> Void
    var isLoading: Bool = false
    var style: Style = .filled
    var tint: Color = DesignColors.primary

    enum Style { case filled, bordered }

    init(_ titleKey: LocalizedStringKey,
         systemImage: String? = nil,
         isLoading: Bool = false,
         style: Style = .filled,
         tint: Color = DesignColors.primary,
         action: @escaping () -> Void) {
        self.titleKey = titleKey
        self.systemImage = systemImage
        self.isLoading = isLoading
        self.style = style
        self.tint = tint
        self.action = action
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: DesignSpacing.sm) {
                if isLoading {
                    ProgressView().tint(foreground)
                } else if let systemImage {
                    Image(systemName: systemImage)
                }
                Text(titleKey).font(DesignTypography.headline)
            }
            .frame(maxWidth: .infinity, minHeight: 56)
            .foregroundStyle(foreground)
            .background(background)
            .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
        }
        .disabled(isLoading)
        .accessibilityAddTraits(.isButton)
        .frame(minWidth: 44, minHeight: 44)
    }

    private var foreground: Color {
        style == .filled ? .white : tint
    }

    @ViewBuilder
    private var background: some View {
        switch style {
        case .filled:
            tint
        case .bordered:
            RoundedRectangle(cornerRadius: DesignRadius.md)
                .stroke(tint, lineWidth: 2)
        }
    }
}

#Preview {
    VStack(spacing: 16) {
        PrimaryButton("common.start", systemImage: "camera.fill") {}
        PrimaryButton("common.cancel", style: .bordered) {}
    }
    .padding()
}
