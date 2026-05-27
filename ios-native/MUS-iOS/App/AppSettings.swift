import SwiftUI

/// 使用者偏好設定：字體大小、主題色票
/// 對應舊版 index.html 的「設定面板」功能
@MainActor
final class AppSettings: ObservableObject {
    enum FontScale: String, CaseIterable, Identifiable {
        case normal, medium, large
        var id: String { rawValue }
        var titleKey: LocalizedStringKey {
            switch self {
            case .normal: return "settings.font.normal"
            case .medium: return "settings.font.medium"
            case .large:  return "settings.font.large"
            }
        }
        /// 字體縮放倍率（套用於 DesignTypography）
        var multiplier: CGFloat {
            switch self {
            case .normal: return 1.0
            case .medium: return 1.15
            case .large:  return 1.30
            }
        }
        /// Dynamic Type 對應，讓系統元件（List/Form）也跟著放大
        var dynamicTypeSize: DynamicTypeSize {
            switch self {
            case .normal: return .large
            case .medium: return .xLarge
            case .large:  return .xxLarge
            }
        }
    }

    enum Theme: String, CaseIterable, Identifiable {
        case system, light, warm, dark
        var id: String { rawValue }
        var titleKey: LocalizedStringKey {
            switch self {
            case .system: return "settings.theme.system"
            case .light:  return "settings.theme.light"
            case .warm:   return "settings.theme.warm"
            case .dark:   return "settings.theme.dark"
            }
        }
        /// 強制 colorScheme；system 回 nil 跟隨系統
        var colorScheme: ColorScheme? {
            switch self {
            case .system: return nil
            case .light, .warm: return .light
            case .dark: return .dark
            }
        }
        /// 主色（覆寫 DesignColors.primary）
        var primaryColor: Color {
            switch self {
            case .system, .light: return Color(red: 0.36, green: 0.46, blue: 0.33)  // 綠
            case .warm: return Color(red: 0.55, green: 0.43, blue: 0.30)            // 暖棕
            case .dark: return Color(red: 0.50, green: 0.45, blue: 0.80)            // 紫
            }
        }
        /// 背景漸層（首頁與主畫面用）
        var backgroundGradient: LinearGradient {
            switch self {
            case .system, .light:
                return LinearGradient(colors: [Color(red: 0.91, green: 0.95, blue: 0.89),
                                               Color(red: 0.97, green: 0.99, blue: 0.95)],
                                      startPoint: .top, endPoint: .bottom)
            case .warm:
                return LinearGradient(colors: [Color(red: 0.99, green: 0.96, blue: 0.91),
                                               Color(red: 0.96, green: 0.92, blue: 0.85)],
                                      startPoint: .top, endPoint: .bottom)
            case .dark:
                return LinearGradient(colors: [Color(red: 0.06, green: 0.05, blue: 0.16),
                                               Color(red: 0.19, green: 0.17, blue: 0.39),
                                               Color(red: 0.14, green: 0.14, blue: 0.24)],
                                      startPoint: .topLeading, endPoint: .bottomTrailing)
            }
        }
    }

    @Published var fontScale: FontScale {
        didSet { UserDefaults.standard.set(fontScale.rawValue, forKey: Self.fontKey) }
    }

    @Published var theme: Theme {
        didSet { UserDefaults.standard.set(theme.rawValue, forKey: Self.themeKey) }
    }

    private static let fontKey = "appSettings.fontScale"
    private static let themeKey = "appSettings.theme"

    init() {
        let f = UserDefaults.standard.string(forKey: Self.fontKey).flatMap(FontScale.init(rawValue:)) ?? .normal
        let t = UserDefaults.standard.string(forKey: Self.themeKey).flatMap(Theme.init(rawValue:)) ?? .system
        self.fontScale = f
        self.theme = t
    }
}
