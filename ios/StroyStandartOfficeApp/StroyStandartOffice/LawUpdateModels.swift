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
