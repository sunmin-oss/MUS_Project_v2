import SwiftUI

/// AI 藥物諮詢聊天介面
struct AIChatView: View {
    @EnvironmentObject private var env: AppEnvironment
    @EnvironmentObject private var settings: AppSettings
    @State private var messages: [ChatMessage] = []
    @State private var inputText = ""
    @State private var isLoading = false
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            // AI 警語 Banner
            aiDisclaimerBanner

            // 聊天內容
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: DesignSpacing.sm) {
                        ForEach(messages) { msg in
                            ChatBubble(message: msg)
                                .id(msg.id)
                        }
                        if isLoading {
                            HStack {
                                TypingIndicator()
                                Spacer()
                            }
                            .padding(.horizontal, DesignSpacing.md)
                        }
                    }
                    .padding(.vertical, DesignSpacing.sm)
                }
                .onChange(of: messages.count) { _ in
                    if let last = messages.last {
                        withAnimation { proxy.scrollTo(last.id, anchor: .bottom) }
                    }
                }
            }

            Divider()

            // 輸入區
            inputBar
        }
        .background(Color(.systemGroupedBackground))
        .navigationTitle("AI 藥物諮詢")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { addWelcomeMessage() }
    }

    // MARK: - AI 免責警語

    private var aiDisclaimerBanner: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "exclamationmark.triangle.fill")
                .foregroundStyle(.orange)
                .font(.system(size: 14))
            Text("AI 提供的資訊僅供參考，不構成醫療建議。如有用藥疑問，請諮詢專業藥師或醫師。")
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.horizontal, DesignSpacing.md)
        .padding(.vertical, 10)
        .background(Color.orange.opacity(0.08))
    }

    // MARK: - 輸入列

    private var inputBar: some View {
        HStack(spacing: 10) {
            TextField("輸入藥物相關問題...", text: $inputText, axis: .vertical)
                .textFieldStyle(.plain)
                .lineLimit(1...4)
                .focused($isInputFocused)
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color(.secondarySystemBackground))
                )

            Button {
                sendMessage()
            } label: {
                Image(systemName: "arrow.up.circle.fill")
                    .font(.system(size: 32))
                    .foregroundStyle(inputText.trimmingCharacters(in: .whitespaces).isEmpty
                                    ? Color.gray.opacity(0.4)
                                    : DesignColors.primary)
            }
            .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty || isLoading)
        }
        .padding(.horizontal, DesignSpacing.md)
        .padding(.vertical, 10)
        .background(.ultraThinMaterial)
    }

    // MARK: - Logic

    private func addWelcomeMessage() {
        guard messages.isEmpty else { return }
        messages.append(ChatMessage(
            role: .assistant,
            content: "您好！我是 AI 藥物諮詢助手。您可以詢問我關於藥物用法、副作用、交互作用等問題。\n\n⚠️ 請注意：我的回答僅供參考，無法取代專業醫療人員的診斷與建議。"
        ))
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespaces)
        guard !text.isEmpty else { return }

        let userMsg = ChatMessage(role: .user, content: text)
        messages.append(userMsg)
        inputText = ""
        isLoading = true

        Task {
            let reply = await getAIResponse(query: text)
            messages.append(ChatMessage(role: .assistant, content: reply))
            isLoading = false
        }
    }

    private func getAIResponse(query: String) async -> String {
        // 嘗試呼叫後端 AI API
        do {
            guard let client = env.apiClient as? RealAPIClient else {
                return mockAIResponse(query: query)
            }
            return try await client.askAI(question: query)
        } catch {
            return "抱歉，目前無法連接 AI 服務。請稍後再試，或直接諮詢藥師。\n\n（錯誤：\(error.localizedDescription)）"
        }
    }

    private func mockAIResponse(query: String) -> String {
        // Demo 模式的模擬回覆
        let responses = [
            "根據您的問題，以下是一些參考資訊：\n\n一般而言，服藥時間應遵照醫囑。如為飯後服用的藥物，建議在餐後 30 分鐘內服用。\n\n⚠️ 此為 AI 生成內容，僅供參考。",
            "這是一個很好的問題。藥物之間確實可能存在交互作用，建議您：\n\n1. 將所有正在服用的藥物告知醫師或藥師\n2. 不要自行停藥或調整劑量\n3. 如有不適，請立即就醫\n\n⚠️ 此為 AI 生成內容，僅供參考。",
            "根據一般藥學資訊，此藥物常見的副作用包括：頭暈、噁心、疲倦等。如果症狀持續或加重，請諮詢您的醫師。\n\n⚠️ 此為 AI 生成內容，僅供參考。"
        ]
        return responses.randomElement() ?? responses[0]
    }
}

// MARK: - ChatMessage Model

struct ChatMessage: Identifiable {
    let id = UUID()
    let role: Role
    let content: String
    let timestamp = Date()

    enum Role { case user, assistant }
}

// MARK: - ChatBubble

private struct ChatBubble: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if message.role == .user { Spacer(minLength: 48) }

            if message.role == .assistant {
                Image(systemName: "cross.circle.fill")
                    .font(.system(size: 24))
                    .foregroundStyle(DesignColors.primary)
            }

            VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .font(.system(size: 15))
                    .foregroundStyle(message.role == .user ? .white : DesignColors.textPrimary)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 18)
                            .fill(message.role == .user
                                  ? DesignColors.primary
                                  : Color(.secondarySystemBackground))
                    )

                if message.role == .assistant {
                    HStack(spacing: 4) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 9))
                        Text("AI 生成")
                            .font(.system(size: 10))
                    }
                    .foregroundStyle(.orange.opacity(0.8))
                }
            }

            if message.role == .assistant { Spacer(minLength: 48) }
        }
        .padding(.horizontal, DesignSpacing.md)
    }
}

// MARK: - TypingIndicator

private struct TypingIndicator: View {
    @State private var phase = 0

    var body: some View {
        HStack(spacing: 4) {
            Image(systemName: "cross.circle.fill")
                .font(.system(size: 24))
                .foregroundStyle(DesignColors.primary)
            HStack(spacing: 3) {
                ForEach(0..<3) { i in
                    Circle()
                        .fill(DesignColors.textSecondary)
                        .frame(width: 6, height: 6)
                        .opacity(phase == i ? 1 : 0.3)
                }
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 18)
                    .fill(Color(.secondarySystemBackground))
            )
        }
        .onAppear { startAnimation() }
    }

    private func startAnimation() {
        Timer.scheduledTimer(withTimeInterval: 0.4, repeats: true) { _ in
            withAnimation(.easeInOut(duration: 0.3)) { phase = (phase + 1) % 3 }
        }
    }
}

#Preview {
    NavigationStack {
        AIChatView()
            .environmentObject(AppEnvironment.makeDefault())
            .environmentObject(AppSettings())
    }
}
