import SwiftUI
import MapKit

struct PharmacyDetailView: View {
    let pharmacy: Pharmacy
    @ObservedObject var store: PharmacyStore
    @Environment(\.dismiss) private var dismiss

    @State private var region: MKCoordinateRegion

    init(pharmacy: Pharmacy, store: PharmacyStore) {
        self.pharmacy = pharmacy
        self.store = store
        _region = State(initialValue: MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: pharmacy.latitude, longitude: pharmacy.longitude),
            span: MKCoordinateSpan(latitudeDelta: 0.005, longitudeDelta: 0.005)
        ))
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: DesignSpacing.md) {
                    // Header info
                    VStack(alignment: .leading, spacing: DesignSpacing.sm) {
                        Text(pharmacy.name)
                            .font(DesignTypography.title2)
                            .foregroundStyle(DesignColors.textPrimary)

                        HStack(spacing: DesignSpacing.xs) {
                            Image(systemName: "mappin.circle.fill")
                                .foregroundStyle(DesignColors.primary)
                            Text(pharmacy.address)
                                .font(DesignTypography.body)
                                .foregroundStyle(DesignColors.textSecondary)
                        }

                        HStack(spacing: DesignSpacing.xs) {
                            if pharmacy.isNHIContracted {
                                TagBadge(text: "健保特約", color: DesignColors.primary)
                            }
                            if pharmacy.is24h {
                                TagBadge(text: "24小時", color: .blue)
                            }
                        }
                    }
                    .padding(.horizontal, DesignSpacing.md)

                    // Mini map (non-interactive)
                    Map(coordinateRegion: .constant(region),
                        interactionModes: [],
                        annotationItems: [pharmacy]) { p in
                        MapAnnotation(coordinate: CLLocationCoordinate2D(
                            latitude: p.latitude, longitude: p.longitude)) {
                            Circle()
                                .fill(DesignColors.primary)
                                .frame(width: 20, height: 20)
                                .overlay(Circle().stroke(.white, lineWidth: 3))
                                .shadow(radius: 4)
                        }
                    }
                    .frame(height: 180)
                    .clipShape(RoundedRectangle(cornerRadius: DesignRadius.lg))
                    .padding(.horizontal, DesignSpacing.md)

                    // Action buttons
                    HStack(spacing: DesignSpacing.sm) {
                        actionButton(icon: "phone.fill", label: "撥打電話") {
                            // Demo: show mock number via URL (disabled if no real number)
                        }
                        .opacity(0.5)
                        .disabled(true)

                        actionButton(icon: "map.fill", label: "導航") {
                            let url = URL(string: "maps://?daddr=\(pharmacy.latitude),\(pharmacy.longitude)&dirflg=w")!
                            UIApplication.shared.open(url)
                        }

                        actionButton(
                            icon: store.isFavorite(pharmacy.id) ? "star.fill" : "star",
                            label: store.isFavorite(pharmacy.id) ? "已加入最愛" : "加入最愛",
                            color: store.isFavorite(pharmacy.id) ? .yellow : DesignColors.primary
                        ) {
                            store.toggleFavorite(pharmacy.id)
                        }
                    }
                    .padding(.horizontal, DesignSpacing.md)

                    Divider()
                        .padding(.horizontal, DesignSpacing.md)

                    // Nearby pharmacies section
                    Text("附近藥局")
                        .font(DesignTypography.headline)
                        .foregroundStyle(DesignColors.textPrimary)
                        .padding(.horizontal, DesignSpacing.md)

                    let others = store.pharmacies.filter { $0.id != pharmacy.id }
                    if others.isEmpty {
                        Text("pharmacy.empty")
                            .font(DesignTypography.body)
                            .foregroundStyle(DesignColors.textSecondary)
                            .padding(.horizontal, DesignSpacing.md)
                    } else {
                        VStack(spacing: DesignSpacing.sm) {
                            ForEach(others.prefix(3)) { p in
                                PharmacyRowCard(pharmacy: p, isFavorite: store.isFavorite(p.id))
                                    .padding(.horizontal, DesignSpacing.md)
                            }
                        }
                    }
                }
                .padding(.vertical, DesignSpacing.md)
            }
            .navigationTitle(pharmacy.name)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("general.done") { dismiss() }
                }
            }
        }
    }

    private func actionButton(icon: String, label: String, color: Color = DesignColors.primary, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            VStack(spacing: DesignSpacing.xs) {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundStyle(color)
                Text(label)
                    .font(DesignTypography.caption)
                    .foregroundStyle(DesignColors.textSecondary)
            }
            .frame(maxWidth: .infinity, minHeight: DesignSpacing.minTapTarget)
            .padding(.vertical, DesignSpacing.sm)
            .background(DesignColors.cardBackground)
            .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    PharmacyDetailView(pharmacy: MockData.pharmacies[0], store: {
        let s = PharmacyStore()
        s.pharmacies = MockData.pharmacies
        return s
    }())
}
