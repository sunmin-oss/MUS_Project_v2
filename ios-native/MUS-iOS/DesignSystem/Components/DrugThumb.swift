import SwiftUI

struct DrugThumb: View {
    let url: URL?
    var size: CGFloat = 48
    var zoomable: Bool = true
    @State private var showFullImage = false

    var body: some View {
        Group {
            if let url {
                AsyncImage(url: url) { phase in
                    switch phase {
                    case .empty:
                        ProgressView()
                    case .success(let image):
                        image.resizable().scaledToFill()
                    case .failure:
                        placeholder
                    @unknown default:
                        placeholder
                    }
                }
            } else {
                placeholder
            }
        }
        .frame(width: size, height: size)
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 10, style: .continuous)
                .stroke(Color.secondary.opacity(0.15), lineWidth: 0.5)
        )
        .onTapGesture {
            if zoomable && url != nil { showFullImage = true }
        }
        .fullScreenCover(isPresented: $showFullImage) {
            DrugImageViewer(url: url)
        }
    }

    private var placeholder: some View {
        ZStack {
            Color(.secondarySystemBackground)
            Image(systemName: "pills.fill")
                .font(.system(size: size * 0.5))
                .foregroundStyle(DesignColors.primary)
        }
    }
}

struct DrugImageViewer: View {
    let url: URL?
    @Environment(\.dismiss) private var dismiss
    @State private var scale: CGFloat = 1.0

    var body: some View {
        NavigationStack {
            ZStack {
                Color.black.ignoresSafeArea()
                if let url {
                    AsyncImage(url: url) { phase in
                        switch phase {
                        case .success(let image):
                            image
                                .resizable()
                                .scaledToFit()
                                .scaleEffect(scale)
                                .gesture(
                                    MagnificationGesture()
                                        .onChanged { value in scale = value }
                                        .onEnded { _ in
                                            withAnimation { scale = max(1.0, min(scale, 5.0)) }
                                        }
                                )
                                .onTapGesture(count: 2) {
                                    withAnimation { scale = scale > 1.0 ? 1.0 : 3.0 }
                                }
                        case .empty:
                            ProgressView().tint(.white)
                        default:
                            Image(systemName: "photo")
                                .font(.largeTitle)
                                .foregroundStyle(.white)
                        }
                    }
                }
            }
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .font(.title2)
                            .foregroundStyle(.white.opacity(0.8))
                    }
                }
            }
            .toolbarBackground(.hidden, for: .navigationBar)
        }
    }
}
