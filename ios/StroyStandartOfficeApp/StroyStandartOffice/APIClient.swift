import Foundation

final class APIClient: ObservableObject {
    @Published var baseURL: String = UserDefaults.standard.string(forKey: "api_base_url") ?? "http://192.168.0.107:8787" {
        didSet {
            UserDefaults.standard.set(baseURL, forKey: "api_base_url")
        }
    }

    private let jsonDecoder = JSONDecoder()
    private let knownFallbackBaseURLs = [
        "http://192.168.0.107:8787",
        "http://localhost:8787",
        "http://127.0.0.1:8787",
    ]

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
        throw lastError ?? URLError(.cannotConnectToHost)
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
}
