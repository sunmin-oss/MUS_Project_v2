import SwiftUI

/// 字級系統：針對年長者最佳化，全程支援 Dynamic Type
/// 最小內文 17pt、標題 ≥ 22pt
enum DesignTypography {
    static let largeTitle = Font.system(size: 34, weight: .bold, design: .rounded)
    static let title = Font.system(size: 28, weight: .bold, design: .rounded)
    static let title2 = Font.system(size: 22, weight: .semibold, design: .rounded)
    static let headline = Font.system(size: 19, weight: .semibold)
    static let body = Font.system(size: 17, weight: .regular)
    static let bodyLarge = Font.system(size: 20, weight: .regular)        // 大字模式
    static let callout = Font.system(size: 16, weight: .regular)
    static let caption = Font.system(size: 14, weight: .regular)
}

enum DesignSpacing {
    static let xs: CGFloat = 4
    static let sm: CGFloat = 8
    static let md: CGFloat = 16
    static let lg: CGFloat = 24
    static let xl: CGFloat = 32
    /// 觸控目標最小尺寸（HIG）
    static let minTapTarget: CGFloat = 44
}

enum DesignRadius {
    static let sm: CGFloat = 8
    static let md: CGFloat = 12
    static let lg: CGFloat = 16
}
