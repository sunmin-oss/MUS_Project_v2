import SwiftUI
import Combine

@MainActor
final class ServerStatusChecker: ObservableObject {
    @Published var isOnline = false
    @Published var visionAvailable = false
    private var timer: Timer?
    private let baseURL: URL

    init(baseURL: URL) {
        self.baseURL = baseURL
    }

    func startMonitoring() {
        check()
        timer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                self?.check()
            }
        }
    }

    func stopMonitoring() {
        timer?.invalidate()
        timer = nil
    }

    func check() {
        let url = baseURL.appendingPathComponent("api/health")
        var req = URLRequest(url: url)
        req.timeoutInterval = 5
        Task {
            do {
                print("[ServerStatus] Checking \(url.absoluteString)...")
                let (data, resp) = try await URLSession.shared.data(for: req)
                guard let http = resp as? HTTPURLResponse else {
                    print("[ServerStatus] No HTTP response")
                    isOnline = false
                    visionAvailable = false
                    return
                }
                print("[ServerStatus] HTTP \(http.statusCode)")
                guard http.statusCode == 200 else {
                    isOnline = false
                    visionAvailable = false
                    return
                }
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let services = json["services"] as? [String: String] {
                    isOnline = true
                    visionAvailable = services["vision_api"] == "ready"
                } else {
                    isOnline = true
                    visionAvailable = false
                }
                print("[ServerStatus] Online=\(isOnline), Vision=\(visionAvailable)")
            } catch {
                print("[ServerStatus] Error: \(error.localizedDescription)")
                isOnline = false
                visionAvailable = false
            }
        }
    }
}
