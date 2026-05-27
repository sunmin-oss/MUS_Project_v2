import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var env: AppEnvironment

    var body: some View {
        NavigationStack {
            Form {
                Section("profile.section.account") {
                    Label("profile.guest", systemImage: "person.crop.circle")
                        .font(DesignTypography.body)
                }

                Section("profile.section.settings") {
                    Toggle(isOn: $env.isDemoMode) {
                        Label("profile.demo.mode", systemImage: "theatermasks.fill")
                            .font(DesignTypography.body)
                    }
                    NavigationLink {
                        Text("profile.coming.soon").font(DesignTypography.body)
                    } label: {
                        Label("profile.notifications", systemImage: "bell.fill")
                            .font(DesignTypography.body)
                    }
                }

                Section("profile.section.about") {
                    HStack {
                        Label("profile.version", systemImage: "info.circle")
                        Spacer()
                        Text(appVersion).foregroundStyle(DesignColors.textSecondary)
                    }
                    .font(DesignTypography.body)
                }
            }
            .navigationTitle("tab.profile")
        }
    }

    private var appVersion: String {
        let v = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "1.0.0"
        let b = Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "1"
        return "\(v) (\(b))"
    }
}

#Preview {
    ProfileView().environmentObject(AppEnvironment.makeDefault())
}
