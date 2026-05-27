import SwiftUI
import MapKit
import CoreLocation

// MARK: - LocationManager

extension CLLocationCoordinate2D: @retroactive Equatable {
    public static func == (lhs: CLLocationCoordinate2D, rhs: CLLocationCoordinate2D) -> Bool {
        lhs.latitude == rhs.latitude && lhs.longitude == rhs.longitude
    }
}

final class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    private let manager = CLLocationManager()
    @Published var coordinate: CLLocationCoordinate2D?
    @Published var authorizationStatus: CLAuthorizationStatus = .notDetermined

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters
        authorizationStatus = manager.authorizationStatus
    }

    func requestPermissionAndLocation() {
        manager.requestWhenInUseAuthorization()
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        if authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways {
            manager.requestLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        coordinate = locations.first?.coordinate
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {}
}

// MARK: - PharmacyMapView

private let defaultCoordinate = CLLocationCoordinate2D(latitude: 25.0478, longitude: 121.5170)
private let defaultSpan = MKCoordinateSpan(latitudeDelta: 0.04, longitudeDelta: 0.04)

struct PharmacyMapView: View {
    @EnvironmentObject private var env: AppEnvironment
    @StateObject private var store = PharmacyStore()
    @StateObject private var locationManager = LocationManager()

    @State private var region = MKCoordinateRegion(center: defaultCoordinate, span: defaultSpan)
    @State private var selectedPharmacy: Pharmacy?
    @State private var viewMode: ViewMode = .map

    enum ViewMode: String, CaseIterable {
        case map = "地圖"
        case list = "列表"
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Segmented picker: 地圖 / 列表
                Picker("", selection: $viewMode) {
                    ForEach(ViewMode.allCases, id: \.self) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.horizontal, DesignSpacing.md)
                .padding(.vertical, DesignSpacing.sm)
                .background(DesignColors.secondaryBackground)

                if viewMode == .map {
                    mapContent
                } else {
                    PharmacyListView(store: store)
                }
            }
            .navigationTitle("pharmacy.nearby.title")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button {
                        Task { await reload() }
                    } label: {
                        if store.isLoading {
                            ProgressView().frame(width: 20, height: 20)
                        } else {
                            Label("pharmacy.refresh", systemImage: "arrow.clockwise")
                                .labelStyle(.iconOnly)
                        }
                    }
                }
            }
            .sheet(item: $selectedPharmacy) { pharmacy in
                PharmacyDetailView(pharmacy: pharmacy, store: store)
            }
        }
        .onAppear {
            locationManager.requestPermissionAndLocation()
            Task { await loadInitial() }
        }
        .onChange(of: locationManager.coordinate) { coord in
            guard let coord else { return }
            region.center = coord
        }
    }

    // MARK: - Map Content

    @ViewBuilder
    private var mapContent: some View {
        ZStack(alignment: .bottom) {
            Map(coordinateRegion: $region,
                annotationItems: store.filtered) { pharmacy in
                MapAnnotation(coordinate: CLLocationCoordinate2D(
                    latitude: pharmacy.latitude,
                    longitude: pharmacy.longitude)) {
                    PharmacyMapPin(pharmacy: pharmacy, isSelected: selectedPharmacy?.id == pharmacy.id)
                        .onTapGesture { selectedPharmacy = pharmacy }
                }
            }
            .ignoresSafeArea(edges: .horizontal)

            // Bottom horizontal scroll card
            if !store.filtered.isEmpty {
                pharmacyScrollRow
            }
        }
    }

    private var pharmacyScrollRow: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: DesignSpacing.sm) {
                ForEach(store.filtered) { pharmacy in
                    PharmacyRowCard(pharmacy: pharmacy, isFavorite: store.isFavorite(pharmacy.id))
                        .frame(width: 240)
                        .onTapGesture {
                            withAnimation {
                                region.center = CLLocationCoordinate2D(
                                    latitude: pharmacy.latitude,
                                    longitude: pharmacy.longitude)
                            }
                            selectedPharmacy = pharmacy
                        }
                }
            }
            .padding(.horizontal, DesignSpacing.md)
            .padding(.vertical, DesignSpacing.sm)
        }
        .background(.ultraThinMaterial)
    }

    // MARK: - Helpers

    private func loadInitial() async {
        let center = locationManager.coordinate ?? defaultCoordinate
        await store.load(latitude: center.latitude, longitude: center.longitude, apiClient: env.apiClient)
    }

    private func reload() async {
        let center = region.center
        await store.load(latitude: center.latitude, longitude: center.longitude, apiClient: env.apiClient)
    }
}

// MARK: - Map Pin

struct PharmacyMapPin: View {
    let pharmacy: Pharmacy
    let isSelected: Bool

    var body: some View {
        VStack(spacing: 2) {
            ZStack {
                Circle()
                    .fill(isSelected ? DesignColors.primary : DesignColors.primary.opacity(0.85))
                    .frame(width: isSelected ? 44 : 36, height: isSelected ? 44 : 36)
                    .shadow(color: .black.opacity(0.2), radius: 4)
                Image(systemName: "cross.vial.fill")
                    .font(.system(size: isSelected ? 20 : 16))
                    .foregroundStyle(.white)
            }
            // callout label when selected
            if isSelected {
                Text(pharmacy.name)
                    .font(DesignTypography.caption)
                    .foregroundStyle(DesignColors.textPrimary)
                    .padding(.horizontal, DesignSpacing.xs)
                    .padding(.vertical, 2)
                    .background(.ultraThinMaterial)
                    .clipShape(RoundedRectangle(cornerRadius: DesignRadius.sm))
            }
        }
        .animation(.spring(response: 0.3), value: isSelected)
    }
}

#Preview {
    PharmacyMapView()
        .environmentObject(AppEnvironment.makeDefault())
}
