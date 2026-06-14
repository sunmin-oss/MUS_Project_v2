import SwiftUI

/// 設計系統色票
/// 設計準則：日間綠植 / 夜間深紫藍漸變；文字對比度 ≥ 7:1（WCAG AAA）
enum DesignColors {
    static let primary = Color(red: 0.16, green: 0.55, blue: 0.42)      // 深綠（主色）
    static let primaryLight = Color(red: 0.40, green: 0.75, blue: 0.60)
    static let accent = Color(red: 0.95, green: 0.62, blue: 0.20)       // 暖橘（CTA）

    static let background = Color(.systemBackground)
    static let secondaryBackground = Color(.secondarySystemBackground)
    static let cardBackground = Color(.tertiarySystemBackground)

    static let textPrimary = Color(.label)
    static let textSecondary = Color(.secondaryLabel)

    // 安全警示四級（對應 Spec 06）
    static let alertCritical = Color(red: 0.86, green: 0.20, blue: 0.20) // contraindicated
    static let alertMajor = Color(red: 0.93, green: 0.45, blue: 0.20)    // major
    static let alertModerate = Color(red: 0.95, green: 0.75, blue: 0.25) // moderate
    static let alertMinor = Color(red: 0.40, green: 0.60, blue: 0.85)    // minor / info
}
