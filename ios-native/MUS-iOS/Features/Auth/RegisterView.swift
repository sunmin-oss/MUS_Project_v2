import SwiftUI

struct RegisterView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings
    @Environment(\.dismiss) private var dismiss

    @State private var username = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var displayName = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showSuccess = false

    var body: some View {
        ScrollView {
            VStack(spacing: DesignSpacing.lg) {
                Spacer().frame(height: 20)

                VStack(spacing: DesignSpacing.sm) {
                    Image(systemName: "person.crop.circle.badge.plus")
                        .font(.system(size: 56))
                        .foregroundStyle(DesignColors.primary)
                    Text(verbatim: "建立帳號")
                        .font(.system(size: 24, weight: .bold))
                        .foregroundStyle(DesignColors.textPrimary)
                }

                VStack(spacing: DesignSpacing.md) {
                    formField(title: "帳號", placeholder: "3~32 字元（英數字）", text: $username)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .accessibilityIdentifier("register.username")

                    formField(title: "顯示名稱（選填）", placeholder: "例如：小明", text: $displayName)
                        .accessibilityIdentifier("register.displayName")

                    VStack(alignment: .leading, spacing: 6) {
                        Text(verbatim: "密碼")
                            .font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                        SecureField("至少 8 個字元", text: $password)
                            .textFieldStyle(.plain)
                            .padding(12)
                            .background(
                                RoundedRectangle(cornerRadius: 10)
                                    .fill(Color(.secondarySystemBackground))
                            )
                            .accessibilityIdentifier("register.password")
                    }

                    VStack(alignment: .leading, spacing: 6) {
                        Text(verbatim: "確認密碼")
                            .font(DesignTypography.caption)
                            .foregroundStyle(DesignColors.textSecondary)
                        SecureField("再次輸入密碼", text: $confirmPassword)
                            .textFieldStyle(.plain)
                            .padding(12)
                            .background(
                                RoundedRectangle(cornerRadius: 10)
                                    .fill(Color(.secondarySystemBackground))
                            )
                            .accessibilityIdentifier("register.confirmPassword")
                    }

                    if let errorMessage {
                        Text(errorMessage)
                            .font(DesignTypography.caption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }

                    Button {
                        Task { await register() }
                    } label: {
                        HStack {
                            if isLoading {
                                ProgressView().tint(.white)
                            } else {
                                Text(verbatim: "註冊")
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
                    .accessibilityIdentifier("register.submitButton")
                }
                .padding(.horizontal, DesignSpacing.md)
            }
            .padding(DesignSpacing.md)
        }
        .background(settings.theme.backgroundGradient.ignoresSafeArea())
        .navigationTitle("註冊")
        .navigationBarTitleDisplayMode(.inline)
        .alert("註冊成功", isPresented: $showSuccess) {
            Button("前往登入") { dismiss() }
        } message: {
            Text("帳號建立完成，請登入使用")
        }
    }

    private func formField(title: String, placeholder: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(verbatim: title)
                .font(DesignTypography.caption)
                .foregroundStyle(DesignColors.textSecondary)
            TextField(placeholder, text: text)
                .textFieldStyle(.plain)
                .padding(12)
                .background(
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color(.secondarySystemBackground))
                )
        }
    }

    private var canSubmit: Bool {
        let u = username.trimmingCharacters(in: .whitespaces)
        return u.count >= 3 && password.count >= 8 && password == confirmPassword
    }

    @MainActor
    private func register() async {
        isLoading = true
        errorMessage = nil

        let trimmedUsername = username.trimmingCharacters(in: .whitespaces).lowercased()
        let name = displayName.trimmingCharacters(in: .whitespaces)

        guard password == confirmPassword else {
            errorMessage = "兩次密碼輸入不一致"
            isLoading = false
            return
        }

        do {
            guard let client = env.apiClient as? RealAPIClient else {
                errorMessage = "請先關閉 Demo 模式"
                isLoading = false
                return
            }
            try await client.register(username: trimmedUsername,
                                      password: password,
                                      displayName: name.isEmpty ? trimmedUsername : name)
            showSuccess = true
        } catch APIError.conflict {
            errorMessage = "此帳號已被使用，請更換"
        } catch {
            errorMessage = "註冊失敗：\(error.localizedDescription)"
        }
        isLoading = false
    }
}

#Preview {
    NavigationStack {
        RegisterView()
            .environmentObject(AppEnvironment.makeDefault())
            .environmentObject(AppSettings())
    }
}
