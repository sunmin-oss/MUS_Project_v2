import UIKit

/// 本地儲存藥單原始圖片，以 prescriptionLabel 為 key
enum PrescriptionImageStore {
    private static let fileManager = FileManager.default

    private static var imageDir: URL {
        fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("PrescriptionImages", isDirectory: true)
    }

    /// 儲存藥單圖片
    static func save(image: UIImage, forLabel label: String) {
        do {
            try fileManager.createDirectory(at: imageDir, withIntermediateDirectories: true)
            guard let data = image.jpegData(compressionQuality: 0.8) else { return }
            let filename = sanitize(label) + ".jpg"
            let url = imageDir.appendingPathComponent(filename)
            try data.write(to: url, options: [.atomic])
        } catch {
            print("[PrescriptionImageStore] save error: \(error)")
        }
    }

    /// 讀取藥單圖片
    static func load(forLabel label: String) -> UIImage? {
        let filename = sanitize(label) + ".jpg"
        let url = imageDir.appendingPathComponent(filename)
        guard let data = try? Data(contentsOf: url) else { return nil }
        return UIImage(data: data)
    }

    /// 取得所有已存的藥單標籤與圖片
    static func allEntries() -> [(label: String, image: UIImage)] {
        guard let files = try? fileManager.contentsOfDirectory(at: imageDir, includingPropertiesForKeys: nil) else {
            return []
        }
        return files.compactMap { url in
            guard url.pathExtension == "jpg",
                  let data = try? Data(contentsOf: url),
                  let image = UIImage(data: data) else { return nil }
            let label = url.deletingPathExtension().lastPathComponent.replacingOccurrences(of: "_", with: " ")
            return (label: label, image: image)
        }
    }

    /// 刪除藥單圖片
    static func remove(forLabel label: String) {
        let filename = sanitize(label) + ".jpg"
        let url = imageDir.appendingPathComponent(filename)
        try? fileManager.removeItem(at: url)
    }

    private static func sanitize(_ label: String) -> String {
        // 移除檔案系統不安全字元，空白轉底線
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-_"))
        return label.unicodeScalars
            .map { allowed.contains($0) ? String($0) : "_" }
            .joined()
    }
}
