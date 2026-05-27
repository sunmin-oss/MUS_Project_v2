import Foundation

@MainActor
final class AllergyStore: ObservableObject {
    @Published var items: [AllergyItem] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    func load(profileId: String, apiClient: APIClientProtocol) async {
        isLoading = true
        errorMessage = nil
        do {
            items = try await apiClient.fetchAllergyItems(profileId: profileId)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    func add(name: String, profileId: String, apiClient: APIClientProtocol) async throws {
        let item = AllergyItem(id: UUID().uuidString, profileId: profileId, name: name.trimmingCharacters(in: .whitespaces))
        let saved = try await apiClient.addAllergyItem(item)
        items.append(saved)
    }

    func delete(id: String, apiClient: APIClientProtocol) async throws {
        try await apiClient.deleteAllergyItem(id: id)
        items.removeAll { $0.id == id }
    }
}
