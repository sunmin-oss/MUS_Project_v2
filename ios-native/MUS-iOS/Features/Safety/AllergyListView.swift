import SwiftUI

struct AllergyListView: View {
    @EnvironmentObject private var env: AppEnvironment
    @StateObject private var store = AllergyStore()
    @State private var showAddAlert = false
    @State private var newAllergyName = ""
    @State private var errorMessage: String?

    var body: some View {
        Group {
            if store.items.isEmpty && !store.isLoading {
                EmptyStateView(
                    titleKey: "allergy.empty",
                    systemImage: "allergens",
                    messageKey: "allergy.empty"
                )
            } else {
                List {
                    ForEach(store.items) { item in
                        HStack {
                            Image(systemName: "allergens")
                                .foregroundStyle(DesignColors.alertMajor)
                            Text(item.name)
                                .font(DesignTypography.body)
                                .foregroundStyle(DesignColors.textPrimary)
                        }
                        .padding(.vertical, DesignSpacing.xs)
                    }
                    .onDelete { indexSet in
                        Task { await deleteItems(at: indexSet) }
                    }
                }
            }
        }
        .navigationTitle("allergy.list.title")
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button {
                    newAllergyName = ""
                    showAddAlert = true
                } label: {
                    Label("allergy.add.button", systemImage: "plus")
                }
            }
        }
        .alert("allergy.add.button", isPresented: $showAddAlert) {
            TextField("allergy.add.placeholder", text: $newAllergyName)
                .autocorrectionDisabled()
            Button("general.save") {
                guard !newAllergyName.trimmingCharacters(in: .whitespaces).isEmpty else { return }
                Task { await addAllergy() }
            }
            Button("general.cancel", role: .cancel) {}
        } message: {
            Text("allergy.add.placeholder")
        }
        .overlay {
            if let error = errorMessage {
                VStack {
                    Spacer()
                    Text(error)
                        .font(DesignTypography.caption)
                        .padding()
                        .background(.red)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: DesignRadius.sm))
                        .padding()
                }
            }
        }
        .onAppear {
            Task { await store.load(profileId: env.selectedProfileId, apiClient: env.apiClient) }
        }
    }

    private func addAllergy() async {
        do {
            try await store.add(name: newAllergyName, profileId: env.selectedProfileId, apiClient: env.apiClient)
        } catch {
            errorMessage = error.localizedDescription
            DispatchQueue.main.asyncAfter(deadline: .now() + 3) { errorMessage = nil }
        }
    }

    private func deleteItems(at indexSet: IndexSet) async {
        for index in indexSet {
            let item = store.items[index]
            do {
                try await store.delete(id: item.id, apiClient: env.apiClient)
            } catch {
                errorMessage = error.localizedDescription
                DispatchQueue.main.asyncAfter(deadline: .now() + 3) { errorMessage = nil }
            }
        }
    }
}

#Preview {
    NavigationStack {
        AllergyListView()
    }
    .environmentObject(AppEnvironment.makeDefault())
}
