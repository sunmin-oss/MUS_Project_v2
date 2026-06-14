import SwiftUI
import MapKit

// MARK: - PharmacyRowCard (shared between map bottom row and list)

struct PharmacyRowCard: View {
    let pharmacy: Pharmacy
    let isFavorite: Bool

    var body: some View {
        Card {
            VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                HStack {
                    Text(pharmacy.name)
                        .font(DesignTypography.headline)
                        .foregroundStyle(DesignColors.textPrimary)
                        .lineLimit(1)
                    Spacer()
                    if isFavorite {
                        Image(systemName: "star.fill")
                            .foregroundStyle(.yellow)
                            .font(.caption)
                    }
                }
                Text(pharmacy.address)
                    .font(DesignTypography.caption)
                    .foregroundStyle(DesignColors.textSecondary)
                    .lineLimit(1)
                HStack(spacing: DesignSpacing.xs) {
                    if pharmacy.isNHIContracted {
                        TagBadge(text: "健保特約", color: DesignColors.primary)
                    }
                    if pharmacy.is24h {
                        TagBadge(text: "24小時", color: .blue)
                    }
                }
            }
        }
    }
}

// MARK: - PharmacyListView

struct PharmacyListView: View {
    @EnvironmentObject private var env: AppEnvironment
    @ObservedObject var store: PharmacyStore

    var body: some View {
        VStack(spacing: 0) {
            // Filter chips
            filterRow
                .padding(.horizontal, DesignSpacing.md)
                .padding(.vertical, DesignSpacing.sm)
                .background(DesignColors.secondaryBackground)

            if store.filtered.isEmpty {
                EmptyStateView(
                    titleKey: "pharmacy.empty",
                    systemImage: "mappin.slash",
                    messageKey: "pharmacy.empty"
                )
            } else {
                ScrollView {
                    LazyVStack(spacing: DesignSpacing.sm) {
                        ForEach(store.filtered) { pharmacy in
                            NavigationLink {
                                PharmacyDetailView(pharmacy: pharmacy, store: store)
                            } label: {
                                PharmacyRowCard(pharmacy: pharmacy, isFavorite: store.isFavorite(pharmacy.id))
                                    .padding(.horizontal, DesignSpacing.md)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.vertical, DesignSpacing.sm)
                }
            }
        }
    }

    private var filterRow: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: DesignSpacing.sm) {
                FilterChip(label: "全部",
                           isActive: !store.filterNHI && !store.filter24h) {
                    store.filterNHI = false
                    store.filter24h = false
                }
                FilterChip(label: "健保特約",
                           isActive: store.filterNHI) {
                    store.filterNHI.toggle()
                    if store.filterNHI { store.filter24h = false }
                }
                FilterChip(label: "24小時",
                           isActive: store.filter24h) {
                    store.filter24h.toggle()
                    if store.filter24h { store.filterNHI = false }
                }
            }
        }
    }
}

// MARK: - FilterChip

struct FilterChip: View {
    let label: String
    let isActive: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(label)
                .font(DesignTypography.callout)
                .padding(.horizontal, DesignSpacing.md)
                .padding(.vertical, DesignSpacing.xs)
                .background(isActive ? DesignColors.primary : DesignColors.cardBackground)
                .foregroundStyle(isActive ? .white : DesignColors.textPrimary)
                .clipShape(Capsule())
        }
        .buttonStyle(.plain)
    }
}

// MARK: - TagBadge

struct TagBadge: View {
    let text: String
    let color: Color

    var body: some View {
        Text(text)
            .font(DesignTypography.caption)
            .padding(.horizontal, DesignSpacing.sm)
            .padding(.vertical, 2)
            .background(color.opacity(0.15))
            .foregroundStyle(color)
            .clipShape(Capsule())
    }
}

#Preview {
    NavigationStack {
        PharmacyListView(store: {
            let s = PharmacyStore()
            s.pharmacies = MockData.pharmacies
            return s
        }())
        .environmentObject(AppEnvironment.makeDefault())
    }
}
