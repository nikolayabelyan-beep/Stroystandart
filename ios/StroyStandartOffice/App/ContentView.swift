import SwiftUI

struct ContentView: View {
    @StateObject private var api = APIClient()
    @State private var statusText = "Готово"
    @State private var dashboardURL = ""
    @State private var latestInfo = ""

    var body: some View {
        NavigationView {
            Form {
                Section("Подключение") {
                    TextField("API URL", text: $api.baseURL)
                        .textInputAutocapitalization(.never)
                        .disableAutocorrection(true)
                    Button("Проверить соединение") {
                        Task {
                            await checkHealth()
                        }
                    }
                }

                Section("Юридическая база") {
                    Button("Обновить нормативные источники") {
                        Task {
                            await runLawUpdate()
                        }
                    }
                    Button("Показать последний отчет") {
                        Task {
                            await loadLatestLawReport()
                        }
                    }
                    if !latestInfo.isEmpty {
                        Text(latestInfo)
                            .font(.footnote)
                    }
                }

                Section("Дашборд") {
                    Button("Получить ссылку дашборда") {
                        Task {
                            await fetchDashboard()
                        }
                    }
                    if !dashboardURL.isEmpty {
                        Link("Открыть дашборд", destination: URL(string: dashboardURL)!)
                    }
                }

                Section("Статус") {
                    Text(statusText)
                        .font(.footnote)
                }
            }
            .navigationTitle("StroyStandart Office")
        }
    }

    private func checkHealth() async {
        do {
            let response = try await api.health()
            statusText = response.ok ? "API онлайн: \(response.service)" : "API недоступен"
        } catch {
            statusText = "Ошибка соединения: \(error.localizedDescription)"
        }
    }

    private func fetchDashboard() async {
        do {
            let response = try await api.dashboard()
            dashboardURL = response.dashboard_url
            statusText = dashboardURL.isEmpty ? "Ссылка дашборда не найдена" : "Ссылка загружена"
        } catch {
            statusText = "Ошибка: \(error.localizedDescription)"
        }
    }

    private func loadLatestLawReport() async {
        do {
            let response = try await api.lawLatest()
            latestInfo = "Новых: \(response.new_publications), ошибок: \(response.source_errors)"
            statusText = response.exists ? "Последний отчет загружен" : "Отчетов пока нет"
        } catch {
            statusText = "Ошибка: \(error.localizedDescription)"
        }
    }

    private func runLawUpdate() async {
        statusText = "Обновление запущено..."
        do {
            let response = try await api.lawUpdate()
            if response.ok {
                let newCount = response.new_publications ?? 0
                let errCount = response.source_errors ?? 0
                statusText = "Готово. Новых: \(newCount), ошибок: \(errCount)"
            } else {
                statusText = "Ошибка обновления: \(response.error ?? "неизвестно")"
            }
        } catch {
            statusText = "Ошибка: \(error.localizedDescription)"
        }
    }
}
