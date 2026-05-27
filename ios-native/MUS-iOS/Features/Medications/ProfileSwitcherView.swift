import SwiftUI

struct ProfileSwitcherView: View {
    @EnvironmentObject private var env: AppEnvironment
    let profiles: [Profile]

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: DesignSpacing.sm) {
                ForEach(profiles) { profile in
                    Button {
                        env.selectedProfileId = profile.id
                    } label: {
                        HStack(spacing: 6) {
                            Image(systemName: profile.avatarSystemName)
                                .font(.footnote)
                            Text(profile.name)
                                .font(DesignTypography.caption)
                                .fontWeight(env.selectedProfileId == profile.id ? .semibold : .regular)
                        }
                        .padding(.horizontal, DesignSpacing.sm)
                        .padding(.vertical, 8)
                        .background(
                            env.selectedProfileId == profile.id
                                ? DesignColors.primary.opacity(0.15)
                                : Color(UIColor.secondarySystemBackground)
                        )
                        .foregroundStyle(
                            env.selectedProfileId == profile.id
                                ? DesignColors.primary
                                : DesignColors.textSecondary
                        )
                        .clipShape(Capsule())
                        .overlay(
                            Capsule()
                                .strokeBorder(
                                    env.selectedProfileId == profile.id ? DesignColors.primary : Color.clear,
                                    lineWidth: 1.5
                                )
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, DesignSpacing.md)
            .padding(.vertical, DesignSpacing.xs)
        }
    }
}
