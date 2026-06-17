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
    static func save<T: Encodable>(_ value: T, forKey key: String) {
        do {
            try fileManager.createDirectory(at: cacheDir, withIntermediateDirectories: true)
            let data = try JSONEncoder().encode(value)
            let url = cacheDir.appendingPathComponent("\(key).json")
            try data.write(to: url, options: .atomic)
        } catch {
            print("[LocalCache] save error (\(key)): \(error)")
        }
    }

    /// 讀取本地快取
    static func load<T: Decodable>(_ type: T.Type, forKey key: String) -> T? {
        let url = cacheDir.appendingPathComponent("\(key).json")
        guard let data = try? Data(contentsOf: url) else { return nil }
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
}

/// 搜尋歷史管理（UserDefaults）
@MainActor
final class SearchHistoryStore: ObservableObject {
    @Published var history: [String] = []

    private let key = "drug.search.history"
    private let maxCount = 20

    init() {
        history = UserDefaults.standard.stringArray(forKey: key) ?? []
    }

    func add(_ query: String) {
        let trimmed = query.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        history.removeAll { $0 == trimmed }
        history.insert(trimmed, at: 0)
        if history.count > maxCount {
            history = Array(history.prefix(maxCount))
        }
        UserDefaults.standard.set(history, forKey: key)
    }

    func remove(_ query: String) {
        history.removeAll { $0 == query }
        UserDefaults.standard.set(history, forKey: key)
    }

    func clearAll() {
        history.removeAll()
        UserDefaults.standard.removeObject(forKey: key)
    }
}
