import SwiftUI

struct HealthProfileView: View {
    private let conditions: [(key: String, label: String)] = [
        ("pregnant",      "懷孕中"),
        ("breastfeeding", "哺乳中"),
        ("kidney",        "腎功能不全"),
        ("liver",         "肝功能不全"),
        ("heart",         "心臟病"),
        ("diabetes",      "糖尿病"),
        ("hypertension",  "高血壓")
    ]

    @State private var activeConditions: Set<String> = []

    private let userDefaultsKey = "health.conditions"

    var body: some View {
        Form {
            Section {
                ForEach(conditions, id: \.key) { condition in
                    Toggle(isOn: binding(for: condition.key)) {
                        Text(condition.label)
                            .font(DesignTypography.body)
                    }
                    .tint(DesignColors.primary)
                }
            }

            Section {
                HStack(alignment: .top, spacing: DesignSpacing.sm) {
                    Image(systemName: "info.circle")
                        .foregroundStyle(DesignColors.primary)
                    Text("health.profile.note")
                        .font(DesignTypography.caption)
                        .foregroundStyle(DesignColors.textSecondary)
                }
            }
        }
        .navigationTitle("health.profile.title")
        .onAppear { loadConditions() }
    }

    private func binding(for key: String) -> Binding<Bool> {
        Binding(
            get: { activeConditions.contains(key) },
            set: { newValue in
                if newValue {
                    activeConditions.insert(key)
                } else {
                    activeConditions.remove(key)
                }
                saveConditions()
            }
        )
    }

    private func saveConditions() {
        UserDefaults.standard.set(Array(activeConditions), forKey: userDefaultsKey)
    }

    private func loadConditions() {
        let saved = UserDefaults.standard.stringArray(forKey: userDefaultsKey) ?? []
        activeConditions = Set(saved)
    }
}

#Preview {
    NavigationStack {
        HealthProfileView()
    }
}
