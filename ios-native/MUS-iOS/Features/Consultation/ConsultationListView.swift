import SwiftUI

struct ConsultationListView: View {
    @EnvironmentObject private var env: AppEnvironment
    @State private var consultations: [ConsultationSummary] = []

    var body: some View {
        NavigationStack {
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
            .navigationTitle("tab.consultation")
            .task {
                consultations = (try? await env.apiClient.fetchConsultations()) ?? []
            }
        }
    }
}

#Preview {
    ConsultationListView().environmentObject(AppEnvironment.makeDefault())
}
