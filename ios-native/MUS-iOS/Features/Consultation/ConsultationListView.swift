import SwiftUI

struct ConsultationListView: View {
    @EnvironmentObject private var env: AppEnvironment
    @State private var consultations: [ConsultationSummary] = []
    @State private var showAIChat = false

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // AI 諮詢入口
                Button {
                    showAIChat = true
                } label: {
                    HStack(spacing: 12) {
                        ZStack {
                            Circle()
                                .fill(DesignColors.primary.opacity(0.12))
                                .frame(width: 44, height: 44)
                            Image(systemName: "sparkles")
                                .font(.system(size: 20))
                                .foregroundStyle(DesignColors.primary)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text("AI 藥物諮詢")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundStyle(DesignColors.textPrimary)
                            Text("詢問用藥、副作用、交互作用等問題")
                                .font(.system(size: 13))
                                .foregroundStyle(DesignColors.textSecondary)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundStyle(DesignColors.textSecondary)
                    }
                    .padding(DesignSpacing.md)
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color(.secondarySystemBackground))
                    )
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("consultation.ai.entry")
                .padding(.horizontal, DesignSpacing.md)
                .padding(.top, DesignSpacing.sm)

                // AI 警語
                HStack(spacing: 6) {
                    Image(systemName: "info.circle")
                        .font(.system(size: 11))
                    Text("AI 回覆僅供參考，不構成醫療建議")
                        .font(.system(size: 11))
                }
                .foregroundStyle(.orange)
                .padding(.top, 6)
                .padding(.bottom, DesignSpacing.sm)

                Divider()

                // 諮詢列表
                Group {
                    if consultations.isEmpty {
                        EmptyStateView(titleKey: "consultation.empty.title",
                                       systemImage: "bubble.left.and.bubble.right",
                                       messageKey: "consultation.empty.message")
                    } else {
                        List(consultations) { item in
                            VStack(alignment: .leading, spacing: DesignSpacing.xs) {
                                HStack {
                                    Text(item.title).font(DesignTypography.headline)
                                    Spacer()
                                    if item.isAI {
                                        Text("consultation.tag.ai")
                                            .font(DesignTypography.caption)
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(DesignColors.primaryLight.opacity(0.25))
                                            .clipShape(Capsule())
                                    }
                                }
                                Text(item.lastMessagePreview)
                                    .font(DesignTypography.body)
                                    .foregroundStyle(DesignColors.textSecondary)
                                    .lineLimit(1)
                            }
                            .padding(.vertical, 4)
                        }
                        .listStyle(.insetGrouped)
                    }
                }
            }
            .navigationTitle("tab.consultation")
            .navigationDestination(isPresented: $showAIChat) {
                AIChatView()
            }
            .task {
                consultations = (try? await env.apiClient.fetchConsultations()) ?? []
            }
        }
    }
}

#Preview {
    ConsultationListView()
        .environmentObject(AppEnvironment.makeDefault())
        .environmentObject(AppSettings())
}
