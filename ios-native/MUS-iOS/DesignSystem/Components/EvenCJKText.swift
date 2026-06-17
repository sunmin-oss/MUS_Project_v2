import SwiftUI

/// 將 CJK 文字平均分散在固定寬度容器內，
/// 讓不同字數的按鈕在視覺上呈現等寬、字符等距分布。
struct EvenCJKText: View {
    let text: String
    /// 容器寬度；以「最長字數 × 單字寬度」估算，建議 ≈ 26 × 6 = 156。
    var width: CGFloat = 156

    var body: some View {
        let chars = text.map(String.init)
        HStack(spacing: 0) {
            ForEach(Array(chars.enumerated()), id: \.offset) { _, ch in
                Text(ch)
                    .frame(maxWidth: .infinity)
            }
        }
        .frame(width: width)
    }
}

#Preview {
    VStack(spacing: 12) {
        EvenCJKText(text: "拍照辨識藥物")
        EvenCJKText(text: "藥單辨識")
        EvenCJKText(text: "附近藥局")
        EvenCJKText(text: "辨識歷史紀錄")
    }
    .font(.headline)
    .padding()
}
