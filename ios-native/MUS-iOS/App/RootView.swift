import SwiftUI

/// 主畫面 Tab Bar：首頁 / 用藥 / 諮詢 / 我的
struct RootView: View {
    @EnvironmentObject private var env: AppEnvironment
    @State private var selection: Tab = .home

    enum Tab: Hashable { case home, medications, consultation, profile }

    var body: some View {
        TabView(selection: $selection) {
            HomeView()
                .tabItem { Label("tab.home", systemImage: "house.fill") }
                .tag(Tab.home)

            MedicationsListView()
                .tabItem { Label("tab.medications", systemImage: "pills.fill") }
                .tag(Tab.medications)

            ConsultationListView()
                .tabItem { Label("tab.consultation", systemImage: "bubble.left.and.bubble.right.fill") }
                .tag(Tab.consultation)

            ProfileView()
                .tabItem { Label("tab.profile", systemImage: "person.crop.circle.fill") }
                .tag(Tab.profile)
        }
    }
}

#Preview {
    RootView().environmentObject(AppEnvironment.makeDefault())
}
