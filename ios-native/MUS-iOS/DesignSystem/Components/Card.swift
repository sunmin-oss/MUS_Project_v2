import SwiftUI

/// 卡片容器：圓角 + 陰影 + 內距，作為清單/詳情頁的基礎元件
struct Card<Content: View>: View {
    let content: Content

    init(@ViewBuilder content: () -> Content) {
        self.content = content()
    }

    var body: some View {
        content
            .padding(DesignSpacing.md)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(DesignColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignRadius.lg))
            .shadow(color: Color.black.opacity(0.06), radius: 8, x: 0, y: 2)
    }
}

#Preview {
    Card {
        VStack(alignment: .leading, spacing: 8) {
            Text("普拿疼").font(DesignTypography.title2)
            Text("Paracetamol").font(DesignTypography.body)
                .foregroundStyle(DesignColors.textSecondary)
        }
    }
    .padding()
}
