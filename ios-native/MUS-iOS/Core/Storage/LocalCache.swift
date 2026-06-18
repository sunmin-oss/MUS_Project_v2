import Foundation

/// 通用本地 JSON 快取工具
/// 將 Codable 物件存到 Documents 目錄，供離線使用
enum LocalCache {
    private static let fileManager = FileManager.default

    private static var cacheDir: URL {
        fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("MUSCache", isDirectory: true)
    }

    /// 儲存 Codable 資料到本地
    static func save<T: Codable>(_ value: T, forKey key: String) {
        do {
            try fileManager.createDirectory(at: cacheDir, withIntermediateDirectories: true)
            let wrapper = CacheWrapper(value: value)
            let data = try JSONEncoder().encode(wrapper)
            let url = cacheDir.appendingPathComponent("\(key).json")
            try data.write(to: url, options: [.atomic])
        } catch {
            print("[LocalCache] save error (\(key)): \(error)")
        }
    }

    /// 讀取本地快取（支援 TTL 過期檢查）
    /// - Parameter maxAge: 最大存活秒數，nil 表示永不過期
    static func load<T: Codable>(_ type: T.Type, forKey key: String, maxAge: TimeInterval? = nil) -> T? {
        let url = cacheDir.appendingPathComponent("\(key).json")
        guard let data = try? Data(contentsOf: url) else { return nil }
        // 嘗試解析帶時間戳的 wrapper
        if let wrapper = try? JSONDecoder().decode(CacheWrapper<T>.self, from: data) {
            if let maxAge, Date().timeIntervalSince(wrapper.savedAt) > maxAge {
                // 已過期，清除
                try? fileManager.removeItem(at: url)
                return nil
            }
            return wrapper.value
        }
        // 向下相容：舊格式沒有 wrapper，直接解碼
        return try? JSONDecoder().decode(type, from: data)
    }

    /// 刪除指定快取
    static func remove(forKey key: String) {
        let url = cacheDir.appendingPathComponent("\(key).json")
        try? fileManager.removeItem(at: url)
    }

    /// 清除所有快取
    static func clearAll() {
        try? fileManager.removeItem(at: cacheDir)
    }

    /// 清除所有過期的快取檔案
    static func purgeExpired(maxAge: TimeInterval) {
        guard let files = try? fileManager.contentsOfDirectory(at: cacheDir, includingPropertiesForKeys: [.contentModificationDateKey]) else { return }
        let cutoff = Date().addingTimeInterval(-maxAge)
        for file in files {
            if let attrs = try? file.resourceValues(forKeys: [.contentModificationDateKey]),
               let modified = attrs.contentModificationDate,
               modified < cutoff {
                try? fileManager.removeItem(at: file)
            }
        }
    }
}

/// 包裝儲存值和時間戳
private struct CacheWrapper<T: Codable>: Codable {
    let value: T
    let savedAt: Date

    init(value: T, savedAt: Date = Date()) {
        self.value = value
        self.savedAt = savedAt
    }
}

// MARK: - TTL 常數

extension LocalCache {
    /// 搜尋歷史：7 天
    static let searchHistoryTTL: TimeInterval = 7 * 24 * 3600
    /// 搜尋結果快取：3 天
    static let searchResultTTL: TimeInterval = 3 * 24 * 3600
    /// 辨識歷史：30 天
    static let recognitionHistoryTTL: TimeInterval = 30 * 24 * 3600
    /// 用藥/Profile 快取：不過期（每次啟動會向後端更新）
}

/// 搜尋歷史管理（帶時間戳，自動過期）
@MainActor
final class SearchHistoryStore: ObservableObject {
    @Published var history: [SearchHistoryItem] = []

    struct SearchHistoryItem: Codable, Identifiable {
        let id: UUID
        let query: String
        let date: Date

        init(query: String) {
            self.id = UUID()
            self.query = query
            self.date = Date()
        }
    }

    private let key = "drug.search.history"
    private let maxCount = 20

    init() {
        load()
        purgeExpired()
    }

    var queries: [String] { history.map(\.query) }

    func add(_ query: String) {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        history.removeAll { $0.query == trimmed }
        history.insert(SearchHistoryItem(query: trimmed), at: 0)
        if history.count > maxCount {
            history = Array(history.prefix(maxCount))
        }
        save()
    }

    func remove(_ query: String) {
        history.removeAll { $0.query == query }
        save()
    }

    func clearAll() {
        history.removeAll()
        UserDefaults.standard.removeObject(forKey: key)
    }

    /// 清除超過 7 天的搜尋紀錄
    private func purgeExpired() {
        let cutoff = Date().addingTimeInterval(-LocalCache.searchHistoryTTL)
        let before = history.count
        history.removeAll { $0.date < cutoff }
        if history.count != before { save() }
    }

    private func save() {
        if let data = try? JSONEncoder().encode(history) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }

    private func load() {
        // 嘗試新格式（帶時間戳）
        if let data = UserDefaults.standard.data(forKey: key),
           let items = try? JSONDecoder().decode([SearchHistoryItem].self, from: data) {
            history = items
            return
        }
        // 向下相容：舊格式是 [String]
        if let old = UserDefaults.standard.stringArray(forKey: key) {
            history = old.map { SearchHistoryItem(query: $0) }
            save() // 轉存新格式
        }
    }
}
