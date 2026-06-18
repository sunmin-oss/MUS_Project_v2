import SwiftUI

/// 顯示已儲存的藥單圖片列表
struct PrescriptionImagesView: View {
    @State private var entries: [(label: String, image: UIImage)] = []
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        content
            .navigationTitle("藥單圖片")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("關閉") { dismiss() }
                }
            }
            .onAppear {
                entries = PrescriptionImageStore.allEntries()
            }
    }

    @ViewBuilder
    private var content: some View {
        if entries.isEmpty {
            emptyView
        } else {
            listView
        }
    }

    private var emptyView: some View {
        VStack(spacing: DesignSpacing.md) {
            Image(systemName: "doc.text.image")
                .font(.system(size: 48))
                .foregroundStyle(DesignColors.textSecondary)
            Text("尚無藥單圖片")
                .font(DesignTypography.title2)
            Text("透過藥單辨識拍照後，圖片會自動儲存於此")
                .font(DesignTypography.caption)
                .foregroundStyle(DesignColors.textSecondary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .padding(DesignSpacing.lg)
    }

    private var listView: some View {
        List {
            ForEach(entries.indices, id: \.self) { idx in
                imageRow(entries[idx])
            }
            .onDelete { offsets in
                for idx in offsets {
                    PrescriptionImageStore.remove(forLabel: entries[idx].label)
                }
                entries.remove(atOffsets: offsets)
            }
        }
        .listStyle(.insetGrouped)
    }

    @ViewBuilder
    private func imageRow(_ entry: (label: String, image: UIImage)) -> some View {
        NavigationLink {
            PrescriptionImageDetailView(image: entry.image, label: entry.label)
        } label: {
            HStack(spacing: 12) {
                Image(uiImage: entry.image)
                    .resizable()
                    .scaledToFill()
                    .frame(width: 60, height: 60)
                    .clipShape(RoundedRectangle(cornerRadius: 8))

                VStack(alignment: .leading, spacing: 4) {
                    Text(entry.label)
                        .font(DesignTypography.body)
                        .foregroundStyle(DesignColors.textPrimary)
                    Text("點擊查看大圖")
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                }
            }
            .padding(.vertical, 4)
        }
    }
}

struct PrescriptionImageDetailView: View {
    let image: UIImage
    let label: String
    @State private var scale: CGFloat = 1.0

    var body: some View {
        GeometryReader { geo in
            ScrollView([.horizontal, .vertical], showsIndicators: false) {
                Image(uiImage: image)
                    .resizable()
                    .scaledToFit()
                    .frame(width: geo.size.width * scale)
                    .frame(minHeight: geo.size.height)
            }
        }
        .background(Color(UIColor.systemBackground))
        .navigationTitle(label)
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                HStack(spacing: 16) {
                    Button { withAnimation { scale = max(1.0, scale - 0.5) } } label: {
                        Image(systemName: "minus.magnifyingglass")
                    }
                    Button { withAnimation { scale = min(4.0, scale + 0.5) } } label: {
                        Image(systemName: "plus.magnifyingglass")
                    }
                }
            }
        }
    }
}
