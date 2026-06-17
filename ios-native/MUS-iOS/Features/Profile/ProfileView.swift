import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings

    var body: some View {
        NavigationStack {
            Form {
                Section("profile.section.account") {
                    if env.currentUsername != nil {
                        NavigationLink {
                            PersonalInfoView()
                        } label: {
                            HStack {
                                Image(systemName: "person.crop.circle.fill")
                                    .font(.system(size: 36))
                                    .foregroundStyle(DesignColors.primary)
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(env.currentUsername ?? "")
                                        .font(.system(size: 16, weight: .semibold))
                                    Text("點擊編輯個人資訊")
                                        .font(DesignTypography.caption)
                                        .foregroundStyle(DesignColors.textSecondary)
                                }
                                .padding(.leading, 6)
                            }
                            .padding(.vertical, 4)
                        }
                    } else {
                        Label("profile.guest", systemImage: "person.crop.circle")
                            .font(DesignTypography.body)
                    }
                }

                Section("profile.section.appearance") {
                    Picker(selection: $settings.fontScale) {
                        ForEach(AppSettings.FontScale.allCases) { scale in
                            Text(scale.titleKey).tag(scale)
                        }
                    } label: {
                        Label("profile.font.size", systemImage: "textformat.size")
                    }
                    .pickerStyle(.menu)

                    Picker(selection: $settings.theme) {
                        ForEach(AppSettings.Theme.allCases) { theme in
                            Text(theme.titleKey).tag(theme)
                        }
                    } label: {
                        Label("profile.theme", systemImage: "paintbrush.fill")
                    }
                    .pickerStyle(.menu)

                    // 主題色預覽
                    HStack(spacing: DesignSpacing.sm) {
                        Text("profile.theme.preview")
                            .font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                        Spacer()
                        ForEach(AppSettings.Theme.allCases) { theme in
                            Button { settings.theme = theme } label: {
                                Circle()
                                    .fill(theme.primaryColor)
                                    .frame(width: 28, height: 28)
                                    .overlay(
                                        Circle().stroke(.primary,
                                                        lineWidth: settings.theme == theme ? 2 : 0)
                                    )
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }

                Section("profile.section.safety") {
                    NavigationLink {
                        AllergyListView()
                    } label: {
                        Label("allergy.list.title", systemImage: "allergens")
                            .font(DesignTypography.body)
                    }
                    NavigationLink {
                        HealthProfileView()
                    } label: {
                        Label("health.profile.title", systemImage: "heart.text.square.fill")
                            .font(DesignTypography.body)
                    }
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

                if !env.isDemoMode {
                    Section {
                        Button(role: .destructive) {
                            Task { await env.logout() }
                        } label: {
                            HStack {
                                Spacer()
                                Label("登出", systemImage: "rectangle.portrait.and.arrow.right")
                                Spacer()
                            }
                        }
                    }
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
    ProfileView()
        .environmentObject(AppEnvironment.makeDefault())
        .environmentObject(AppSettings())
}
