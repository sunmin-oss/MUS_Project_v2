import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings

    @State private var username = ""
    @State private var password = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showRegister = false

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: DesignSpacing.lg) {
                    Spacer().frame(height: 40)

                    // Logo
                    VStack(spacing: DesignSpacing.sm) {
                        Image(systemName: "pills.circle.fill")
                            .font(.system(size: 72))
                            .foregroundStyle(DesignColors.primary)
                        Text(verbatim: "藥知道")
                            .font(.system(size: 28, weight: .bold))
                            .foregroundStyle(DesignColors.textPrimary)
                        Text(verbatim: "您的智慧用藥管理助手")
                            .font(DesignTypography.body)
                            .foregroundStyle(DesignColors.textSecondary)
                    }

                    Spacer().frame(height: 20)

                    // Form
                    VStack(spacing: DesignSpacing.md) {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(verbatim: "帳號")
                                .font(DesignTypography.caption)
                                .foregroundStyle(DesignColors.textSecondary)
                            TextField("輸入帳號", text: $username)
                                .textFieldStyle(.plain)
                                .autocorrectionDisabled()
                                .textInputAutocapitalization(.never)
                                .padding(12)
                                .background(
                                    RoundedRectangle(cornerRadius: 10)
                                        .fill(Color(.secondarySystemBackground))
                                )
                                .accessibilityIdentifier("auth.username")
                        }

                        VStack(alignment: .leading, spacing: 6) {
                            Text(verbatim: "密碼")
                                .font(DesignTypography.caption)
                                .foregroundStyle(DesignColors.textSecondary)
                            SecureField("輸入密碼", text: $password)
                                .textFieldStyle(.plain)
                                .padding(12)
                                .background(
                                    RoundedRectangle(cornerRadius: 10)
                                        .fill(Color(.secondarySystemBackground))
                                )
                                .accessibilityIdentifier("auth.password")
                        }

                        if let errorMessage {
                            Text(errorMessage)
                                .font(DesignTypography.caption)
                                .foregroundStyle(.red)
                                .multilineTextAlignment(.center)
                        }

                        Button {
                            Task { await login() }
                        } label: {
                            HStack {
                                if isLoading {
                                    ProgressView().tint(.white)
                                } else {
                                    Text(verbatim: "登入")
                                }
                            }
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(
                                RoundedRectangle(cornerRadius: 12)
                                    .fill(canSubmit ? DesignColors.primary : DesignColors.primary.opacity(0.5))
                            )
                        }
                        .disabled(!canSubmit || isLoading)
                        .accessibilityIdentifier("auth.loginButton")

                        HStack {
                            Text(verbatim: "還沒有帳號？")
                                .font(DesignTypography.caption)
                                .foregroundStyle(DesignColors.textSecondary)
                            Button {
                                showRegister = true
                            } label: {
                                Text(verbatim: "立即註冊")
                                    .font(DesignTypography.caption)
                                    .foregroundStyle(DesignColors.primary)
                            }
                        }
                    }
                    .padding(.horizontal, DesignSpacing.md)
                }
                .padding(DesignSpacing.md)
            }
            .background(settings.theme.backgroundGradient.ignoresSafeArea())
            .navigationDestination(isPresented: $showRegister) {
                RegisterView()
            }
        }
    }

    private var canSubmit: Bool {
        !username.trimmingCharacters(in: .whitespaces).isEmpty &&
        !password.isEmpty
    }

    @MainActor
    private func login() async {
        isLoading = true
        errorMessage = nil
        // 如果是 Demo 模式，自動切換為正式模式
        if env.isDemoMode {
            env.isDemoMode = false
        }
        do {
            guard let client = env.apiClient as? RealAPIClient else {
                errorMessage = "登入失敗，請重新啟動 App"
                isLoading = false
                return
            }
            try await client.login(username: username.trimmingCharacters(in: .whitespaces).lowercased(),
                                   password: password)
            env.currentUsername = username.trimmingCharacters(in: .whitespaces).lowercased()
            UserDefaults.standard.set(env.currentUsername, forKey: "currentUsername")
            env.isAuthenticated = true
            // 載入 profile
            if let pid = await AuthStore.shared.profileId(), pid > 0 {
                env.selectedProfileId = String(pid)
            }
        } catch {
            errorMessage = "帳號或密碼錯誤，請重新輸入"
        }
        isLoading = false
    }
}

#Preview {
    LoginView()
        .environmentObject(AppEnvironment.makeDefault())
        .environmentObject(AppSettings())
}
