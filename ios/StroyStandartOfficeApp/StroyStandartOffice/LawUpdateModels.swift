import Foundation

struct HealthResponse: Decodable {
    let ok: Bool
    let service: String
}

struct DashboardResponse: Decodable {
    let dashboard_url: String
}

struct LawLatestResponse: Decodable {
    let exists: Bool
    let new_publications: Int
    let source_errors: Int
    let report_path: String
    let report_excerpt: String
}

struct LawUpdateResponse: Decodable {
    let ok: Bool
    let started: Bool?
    let running: Bool?
    let started_at: String?
    let finished_at: String?
    let report_path: String?
    let new_publications: Int?
    let source_errors: Int?
    let error: String?
}

struct LawUpdateStatusResponse: Decodable {
    let ok: Bool
    let running: Bool
    let started_at: String?
    let finished_at: String?
    let report_path: String?
    let new_publications: Int?
    let source_errors: Int?
    let error: String?
}

struct ServicesStatusResponse: Decodable {
    let ok: Bool
    let api_process: Bool
    let bot_process: Bool
    let api_health: Bool
    let api_ps: String
    let bot_ps: String
    let output: String?
}

struct DirectorMessage: Decodable, Identifiable {
    let id: String
    let role: String
    let content: String
    let created_at: String?
}

struct DirectorHistoryResponse: Decodable {
    let ok: Bool
    let messages: [DirectorMessage]
}

struct DirectorChatResponse: Decodable {
    let ok: Bool
    let reply: String?
    let saved_path: String?
    let messages: [DirectorMessage]?
    let error: String?
}
