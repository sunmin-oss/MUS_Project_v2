import SwiftUI

struct NotificationPermissionView: View {
    @ObservedObject private var notifManager = NotificationManager.shared
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: DesignSpacing.lg) {
                Spacer()

                if notifManager.authorizationStatus == .authorized {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 72))
                        .foregroundStyle(.green)
                    Text("推播通知已開啟")
                        .font(DesignTypography.title)
                    Text("藥知道將在您的用藥時間發送提醒")
                        .font(DesignTypography.body)
                        .foregroundStyle(DesignColors.textSecondary)
                        .multilineTextAlignment(.center)
                } else {
                    Image(systemName: "bell.badge.fill")
                        .font(.system(size: 72))
                        .foregroundStyle(DesignColors.primary)

                    Text("notification.permission.title")
                        .font(DesignTypography.title)

                    Text("notification.permission.desc")
                        .font(DesignTypography.body)
                        .foregroundStyle(DesignColors.textSecondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, DesignSpacing.lg)

                    VStack(alignment: .leading, spacing: DesignSpacing.sm) {
                        benefitRow("bell.fill", "準時服藥提醒")
                        benefitRow("calendar.badge.checkmark", "服藥紀錄自動記錄")
                        benefitRow("cart.badge.plus", "庫存不足自動通知")
                    }
                    .padding(DesignSpacing.md)
                    .background(Color(UIColor.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: DesignRadius.md))
                    .padding(.horizontal, DesignSpacing.lg)
                }

                Spacer()

                if notifManager.authorizationStatus != .authorized {
                    VStack(spacing: DesignSpacing.sm) {
                        PrimaryButton("notification.permission.enable", systemImage: "bell.fill") {
                            Task {
                                _ = await notifManager.requestPermission()
                            }
                        }
                        .padding(.horizontal, DesignSpacing.md)

                        Button("notification.permission.later") {
                            dismiss()
                        }
                        .font(DesignTypography.body)
                        .foregroundStyle(DesignColors.textSecondary)
                    }
                } else {
                    Button("general.done") { dismiss() }
                        .font(DesignTypography.body)
                }

                Spacer()
            }
            .navigationBarTitleDisplayMode(.inline)
            .task { await notifManager.checkAuthorizationStatus() }
        }
    }

    @ViewBuilder
    private func benefitRow(_ icon: String, _ text: String) -> some View {
        HStack(spacing: DesignSpacing.sm) {
            Image(systemName: icon)
                .frame(width: 24)
                .foregroundStyle(DesignColors.primary)
            Text(text)
                .font(DesignTypography.body)
        }
    }
}
