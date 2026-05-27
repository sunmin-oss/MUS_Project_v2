import SwiftUI

extension View {
    /// Apply elderly-friendly minimum touch target (44x44pt)
    func elderlyTouchTarget() -> some View {
        self.frame(minWidth: 44, minHeight: 44)
    }

    /// Apply standard card accessibility grouping
    func accessibleCard(label: String, hint: String = "") -> some View {
        self
            .accessibilityElement(children: .combine)
            .accessibilityLabel(label)
            .accessibilityHint(hint.isEmpty ? "" : hint)
    }
}
