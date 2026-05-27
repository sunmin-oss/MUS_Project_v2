import Foundation
import CoreLocation

@MainActor
final class PharmacyStore: ObservableObject {
    @Published var pharmacies: [Pharmacy] = []
    @Published var favorites: Set<String> = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    @Published var filterNHI = false
    @Published var filter24h = false

    private let favoritesKey = "pharmacy.favorites"

    init() {
        loadFavorites()
    }

    var filtered: [Pharmacy] {
        pharmacies.filter {
            (!filterNHI || $0.isNHIContracted) && (!filter24h || $0.is24h)
        }
    }

    func load(latitude: Double, longitude: Double, apiClient: APIClientProtocol) async {
        isLoading = true
        errorMessage = nil
        do {
            pharmacies = try await apiClient.fetchNearbyPharmacies(latitude: latitude, longitude: longitude, radius: 2000)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func toggleFavorite(_ id: String) {
        if favorites.contains(id) {
            favorites.remove(id)
        } else {
            favorites.insert(id)
        }
        saveFavorites()
    }

    func isFavorite(_ id: String) -> Bool {
        favorites.contains(id)
    }

    private func saveFavorites() {
        UserDefaults.standard.set(Array(favorites), forKey: favoritesKey)
    }

    private func loadFavorites() {
        let saved = UserDefaults.standard.stringArray(forKey: favoritesKey) ?? []
        favorites = Set(saved)
    }
}
