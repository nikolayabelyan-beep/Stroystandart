import Foundation

final class APIClient: ObservableObject {
    @Published var baseURL: String = "http://127.0.0.1:8787"

    private func makeURL(_ path: String) throws -> URL {
        guard let url = URL(string: baseURL + path) else {
            throw URLError(.badURL)
        }
        return url
    }

    func health() async throws -> HealthResponse {
        let (data, _) = try await URLSession.shared.data(from: try makeURL("/health"))
        return try JSONDecoder().decode(HealthResponse.self, from: data)
    }

    func dashboard() async throws -> DashboardResponse {
        let (data, _) = try await URLSession.shared.data(from: try makeURL("/dashboard-url"))
        return try JSONDecoder().decode(DashboardResponse.self, from: data)
    }

    func lawLatest() async throws -> LawLatestResponse {
        let (data, _) = try await URLSession.shared.data(from: try makeURL("/law/latest"))
        return try JSONDecoder().decode(LawLatestResponse.self, from: data)
    }

    func lawUpdate() async throws -> LawUpdateResponse {
        var request = URLRequest(url: try makeURL("/law/update"))
        request.httpMethod = "POST"
        let (data, _) = try await URLSession.shared.data(for: request)
        return try JSONDecoder().decode(LawUpdateResponse.self, from: data)
    }
}
