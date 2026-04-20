import Foundation
import Darwin

final class APIClient: ObservableObject {
    @Published var baseURL: String = UserDefaults.standard.string(forKey: "api_base_url") ?? "http://127.0.0.1:8787" {
        didSet {
            UserDefaults.standard.set(baseURL, forKey: "api_base_url")
        }
    }

    private let jsonDecoder = JSONDecoder()
    private let knownFallbackBaseURLs = [
        "http://localhost:8787",
        "http://127.0.0.1:8787",
    ]

    struct AutoConnectResult {
        let baseURL: String
        let discoveredOnLAN: Bool
        let status: ServicesStatusResponse
    }

    private func execute<T: Decodable>(_ request: URLRequest, as type: T.Type) async throws -> T {
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw URLError(.badServerResponse)
        }
        guard (200...299).contains(http.statusCode) else {
            if let apiError = try? jsonDecoder.decode(LawUpdateResponse.self, from: data),
               let message = apiError.error,
               !message.isEmpty {
                throw NSError(domain: "APIError", code: http.statusCode, userInfo: [NSLocalizedDescriptionKey: message])
            }
            throw NSError(
                domain: "APIError",
                code: http.statusCode,
                userInfo: [NSLocalizedDescriptionKey: "HTTP \(http.statusCode)"]
            )
        }
        return try jsonDecoder.decode(type, from: data)
    }

    private func normalizeBase(_ raw: String) -> String {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        let normalizedBase = trimmed.hasSuffix("/") ? String(trimmed.dropLast()) : trimmed
        return normalizedBase
    }

    private func makeURL(_ path: String, base: String? = nil) throws -> URL {
        let normalizedBase = normalizeBase(base ?? baseURL)
        guard let url = URL(string: normalizedBase + path) else {
            throw URLError(.badURL)
        }
        return url
    }

    private func candidateBases() -> [String] {
        var unique: [String] = []
        let primary = normalizeBase(baseURL)
        for candidate in [primary] + knownFallbackBaseURLs {
            let normalized = normalizeBase(candidate)
            if !unique.contains(normalized) {
                unique.append(normalized)
            }
        }
        return unique
    }

    private func executeWithFallback<T: Decodable>(
        path: String,
        method: String = "GET",
        timeout: TimeInterval = 15,
        as type: T.Type
    ) async throws -> T {
        var lastError: Error?
        for base in candidateBases() {
            do {
                var request = URLRequest(url: try makeURL(path, base: base))
                request.httpMethod = method
                request.timeoutInterval = timeout
                let decoded: T = try await execute(request, as: type)
                if normalizeBase(baseURL) != base {
                    await MainActor.run {
                        self.baseURL = base
                    }
                }
                return decoded
            } catch {
                lastError = error
            }
        }

        // If simple fallbacks failed, try active LAN discovery once.
        if let discoveredBase = await discoverLANBaseURL() {
            do {
                var request = URLRequest(url: try makeURL(path, base: discoveredBase))
                request.httpMethod = method
                request.timeoutInterval = timeout
                let decoded: T = try await execute(request, as: type)
                if normalizeBase(baseURL) != discoveredBase {
                    await MainActor.run {
                        self.baseURL = discoveredBase
                    }
                }
                return decoded
            } catch {
                lastError = error
            }
        }

        throw lastError ?? URLError(.cannotConnectToHost)
    }

    private static func normalizeStaticBase(_ raw: String) -> String {
        let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.hasSuffix("/") ? String(trimmed.dropLast()) : trimmed
    }

    private static func makeStaticURL(base: String, path: String) -> URL? {
        URL(string: normalizeStaticBase(base) + path)
    }

    private static func probeHealth(base: String, timeout: TimeInterval) async -> Bool {
        guard let url = makeStaticURL(base: base, path: "/health") else {
            return false
        }
        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.timeoutInterval = timeout
        do {
            let (_, response) = try await URLSession.shared.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                return false
            }
            return (200...299).contains(http.statusCode)
        } catch {
            return false
        }
    }

    private static func localIPv4Candidates() -> [String] {
        var addresses: [String] = []
        var ptr: UnsafeMutablePointer<ifaddrs>?
        guard getifaddrs(&ptr) == 0, let first = ptr else {
            return addresses
        }
        defer { freeifaddrs(ptr) }

        var current = first
        while true {
            let interface = current.pointee
            guard let addr = interface.ifa_addr else {
                if let next = interface.ifa_next {
                    current = next
                    continue
                } else {
                    break
                }
            }
            let family = addr.pointee.sa_family
            let name = String(cString: interface.ifa_name)
            if family == UInt8(AF_INET), (name == "en0" || name == "en1" || name == "bridge100") {
                var host = [CChar](repeating: 0, count: Int(NI_MAXHOST))
                let result = getnameinfo(
                    addr,
                    socklen_t(addr.pointee.sa_len),
                    &host,
                    socklen_t(host.count),
                    nil,
                    0,
                    NI_NUMERICHOST
                )
                if result == 0 {
                    let ip = String(cString: host)
                    if ip != "127.0.0.1", !ip.isEmpty {
                        addresses.append(ip)
                    }
                }
            }

            if let next = interface.ifa_next {
                current = next
            } else {
                break
            }
        }

        return Array(Set(addresses)).sorted()
    }

    private static func lanDiscoveryBases() -> [String] {
        var candidates: [String] = []
        let preferredHosts = [2, 10, 20, 30, 40, 50, 80, 90, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 150, 200, 210, 220, 230, 240, 250, 254]

        for ip in localIPv4Candidates() {
            let parts = ip.split(separator: ".")
            guard parts.count == 4 else { continue }
            let prefix = "\(parts[0]).\(parts[1]).\(parts[2])"

            for h in preferredHosts {
                candidates.append("http://\(prefix).\(h):8787")
            }
            for h in 1...254 {
                candidates.append("http://\(prefix).\(h):8787")
            }
        }

        var unique: [String] = []
        for candidate in candidates.map(normalizeStaticBase) {
            if !unique.contains(candidate) {
                unique.append(candidate)
            }
        }
        return unique
    }

    private func discoverLANBaseURL() async -> String? {
        let candidates = Self.lanDiscoveryBases()
        if candidates.isEmpty {
            return nil
        }

        return await withTaskGroup(of: String?.self) { group in
            for candidate in candidates {
                group.addTask {
                    let ok = await Self.probeHealth(base: candidate, timeout: 0.6)
                    return ok ? candidate : nil
                }
            }

            for await found in group {
                if let base = found {
                    group.cancelAll()
                    return base
                }
            }
            return nil
        }
    }

    func autoConnectAndEnsureServices() async throws -> AutoConnectResult {
        var discovered = false
        do {
            _ = try await health()
        } catch {
            if let discoveredBase = await discoverLANBaseURL() {
                await MainActor.run {
                    self.baseURL = discoveredBase
                }
                discovered = true
                _ = try await health()
            } else {
                throw NSError(
                    domain: "APIError",
                    code: -1004,
                    userInfo: [NSLocalizedDescriptionKey: "API не найден в локальной сети. Проверьте, что Mac и iPhone в одной Wi-Fi сети."]
                )
            }
        }

        let status = try await servicesEnsure()
        return AutoConnectResult(
            baseURL: normalizeBase(baseURL),
            discoveredOnLAN: discovered,
            status: status
        )
    }

    func health() async throws -> HealthResponse {
        try await executeWithFallback(path: "/health", timeout: 10, as: HealthResponse.self)
    }

    func dashboard() async throws -> DashboardResponse {
        try await executeWithFallback(path: "/dashboard-url", timeout: 15, as: DashboardResponse.self)
    }

    func lawLatest() async throws -> LawLatestResponse {
        try await executeWithFallback(path: "/law/latest", timeout: 15, as: LawLatestResponse.self)
    }

    func lawUpdate() async throws -> LawUpdateResponse {
        try await executeWithFallback(path: "/law/update", method: "POST", timeout: 15, as: LawUpdateResponse.self)
    }

    func lawUpdateStatus() async throws -> LawUpdateStatusResponse {
        try await executeWithFallback(path: "/law/update-status", timeout: 15, as: LawUpdateStatusResponse.self)
    }

    func servicesStatus() async throws -> ServicesStatusResponse {
        try await executeWithFallback(path: "/services/status", timeout: 12, as: ServicesStatusResponse.self)
    }

    func servicesEnsure() async throws -> ServicesStatusResponse {
        try await executeWithFallback(path: "/services/ensure", method: "POST", timeout: 25, as: ServicesStatusResponse.self)
    }

    func servicesRestart() async throws -> ServicesStatusResponse {
        try await executeWithFallback(path: "/services/restart", method: "POST", timeout: 25, as: ServicesStatusResponse.self)
    }
}
