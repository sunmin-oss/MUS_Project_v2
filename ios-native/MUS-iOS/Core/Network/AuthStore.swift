import Foundation

/// 簡化版 Token 儲存（UserDefaults 而非 Keychain，僅供測試）
/// 正式發布前應改用 Keychain（KeychainAccess pkg or SecKeyChain wrappers）。
actor AuthStore {
    static let shared = AuthStore()

    private let accessKey = "MUS.accessToken"
    private let refreshKey = "MUS.refreshToken"
    private let userIdKey = "MUS.userId"
    private let profileIdKey = "MUS.profileId"

    private var defaults: UserDefaults { .standard }

    func accessToken() -> String? { defaults.string(forKey: accessKey) }
    func refreshToken() -> String? { defaults.string(forKey: refreshKey) }
    func userId() -> Int? {
        let v = defaults.integer(forKey: userIdKey)
        return v == 0 ? nil : v
    }
    func profileId() -> Int? {
        let v = defaults.integer(forKey: profileIdKey)
        return v == 0 ? nil : v
    }

    func setTokens(access: String, refresh: String) {
        defaults.set(access, forKey: accessKey)
        defaults.set(refresh, forKey: refreshKey)
    }
    func setUserId(_ id: Int) { defaults.set(id, forKey: userIdKey) }
    func setProfileId(_ id: Int) { defaults.set(id, forKey: profileIdKey) }
    func clear() {
        [accessKey, refreshKey, userIdKey, profileIdKey].forEach { defaults.removeObject(forKey: $0) }
    }
}

/// 後端常數（測試用固定帳號）
enum BackendConstants {
    static let testUsername = "demo"
    static let testPassword = "Demo1234!"
    static let testDisplayName = "Demo"
}
