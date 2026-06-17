import SwiftUI

struct SpacedButtonStyle: ButtonStyle {
    var filled: Bool = true
    var tint: Color = DesignColors.primary

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .frame(maxWidth: .infinity, minHeight: 56)
            .foregroundStyle(filled ? Color.white : tint)
            .background(
                RoundedRectangle(cornerRadius: DesignRadius.md)
                    .fill(filled ? tint : Color.clear)
                    .overlay(
                        RoundedRectangle(cornerRadius: DesignRadius.md)
                            .stroke(tint, lineWidth: filled ? 0 : 2)
                    )
            )
            .opacity(configuration.isPressed ? 0.7 : 1.0)
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(.easeInOut(duration: 0.15), value: configuration.isPressed)
    }
}

struct SpacedButtonLabel: View {
    let text: String
    let systemImage: String
    var baseCharCount: Int = 6
    var baseTracking: CGFloat = 6

    private var dynamicTracking: CGFloat {
        let count = text.count
        guard count > 0, count < baseCharCount else { return baseTracking }
        let charW: CGFloat = 18
        let totalBase = CGFloat(baseCharCount) * (charW + baseTracking)
        let t = (totalBase / CGFloat(count)) - charW
        return max(baseTracking, t)
    }

    var body: some View {
        HStack(spacing: 10) {
            Image(systemName: systemImage)
                .font(.system(size: 20, weight: .semibold))
            Text(text)
                .font(.system(size: 18, weight: .semibold, design: .rounded))
                .tracking(dynamicTracking)
        }
    }
}
