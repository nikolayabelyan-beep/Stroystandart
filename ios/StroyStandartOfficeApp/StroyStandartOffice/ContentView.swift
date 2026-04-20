import SwiftUI

struct ContentView: View {
    @StateObject private var api = APIClient()
    @State private var statusText = "Готово"
    @State private var dashboardURL = ""
    @State private var latestInfo = ""
    @State private var dashboardLink: URL?
    @State private var isUpdatingLaw = false
    @State private var servicesInfo = ""

    var body: some View {
        NavigationView {
            Form {
                Section("Подключение") {
                    TextField("API URL", text: $api.baseURL)
                        .textInputAutocapitalization(.never)
                        .disableAutocorrection(true)
                    Button("Сбросить URL на Mac (LAN)") {
                        api.baseURL = "http://192.168.0.107:8787"
                        statusText = "URL сброшен на API вашего Mac"
                    }
                    Button("Сбросить URL на localhost") {
                        api.baseURL = "http://127.0.0.1:8787"
                        statusText = "URL сброшен на localhost"
                    }
                    Button("Проверить соединение") {
                        Task {
                            await checkHealth()
                        }
                    }
                }

                Section("Сервисы") {
                    Button("Статус сервисов") {
                        Task {
                            await loadServicesStatus()
                        }
                    }
                    Button("Поднять сервисы") {
                        Task {
                            await ensureServices()
                        }
                    }
                    Button("Перезапустить сервисы") {
                        Task {
                            await restartServices()
                        }
                    }
                    if !servicesInfo.isEmpty {
                        Text(servicesInfo)
                            .font(.footnote)
                    }
                }

                Section("Юридическая база") {
                    Button("Обновить нормативные источники") {
                        Task {
                            await runLawUpdate()
                        }
                    }
                    .disabled(isUpdatingLaw)
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
                    if let dashboardLink {
                        Link("Открыть дашборд", destination: dashboardLink)
                    }
                }

                Section("Статус") {
                    Text(statusText)
                        .font(.footnote)
                }
            }
            .navigationTitle("StroyStandart Office")
            .task {
                await checkHealth()
            }
        }
    }

    private func checkHealth() async {
        do {
            let response = try await api.health()
            statusText = response.ok ? "API онлайн: \(response.service)" : "API недоступен"
        } catch {
            statusText = "Нет связи с API. Нажмите 'Поднять сервисы' в разделе Сервисы."
        }
    }

    private func fetchDashboard() async {
        do {
            let response = try await api.dashboard()
            dashboardURL = response.dashboard_url
            dashboardLink = URL(string: dashboardURL.trimmingCharacters(in: .whitespacesAndNewlines))
            if dashboardLink == nil {
                statusText = "Dashboard пока недоступен (tunnel_url.txt пуст)."
            } else {
                statusText = "Ссылка дашборда загружена"
            }
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
        isUpdatingLaw = true
        statusText = "Обновление запущено в фоне..."
        do {
            let response = try await api.lawUpdate()
            if response.ok, response.running == true {
                statusText = "Идет обновление... проверяю статус"
                await pollLawUpdateStatus()
            } else if response.ok {
                let newCount = response.new_publications ?? 0
                let errCount = response.source_errors ?? 0
                statusText = "Готово. Новых: \(newCount), ошибок: \(errCount)"
                isUpdatingLaw = false
            } else {
                statusText = "Ошибка обновления: \(response.error ?? "неизвестно")"
                isUpdatingLaw = false
            }
        } catch {
            statusText = "Ошибка: \(error.localizedDescription)"
            isUpdatingLaw = false
        }
    }

    private func pollLawUpdateStatus() async {
        for _ in 0..<40 {
            do {
                let status = try await api.lawUpdateStatus()
                if status.running {
                    try? await Task.sleep(nanoseconds: 2_000_000_000)
                    continue
                }
                if let error = status.error, !error.isEmpty {
                    statusText = "Ошибка обновления: \(error)"
                } else {
                    let newCount = status.new_publications ?? 0
                    let errCount = status.source_errors ?? 0
                    statusText = "Готово. Новых: \(newCount), ошибок: \(errCount)"
                    await loadLatestLawReport()
                }
                isUpdatingLaw = false
                return
            } catch {
                statusText = "Ошибка чтения статуса: \(error.localizedDescription)"
                isUpdatingLaw = false
                return
            }
        }
        statusText = "Обновление занимает много времени. Проверьте позже через 'Показать последний отчет'."
        isUpdatingLaw = false
    }

    private func summarizeServices(_ s: ServicesStatusResponse) {
        let api = s.api_process ? "API: up" : "API: down"
        let bot = s.bot_process ? "BOT: up" : "BOT: down"
        let health = s.api_health ? "health: ok" : "health: fail"
        servicesInfo = "\(api), \(bot), \(health)"
    }

    private func loadServicesStatus() async {
        do {
            let status = try await api.servicesStatus()
            summarizeServices(status)
            statusText = "Статус сервисов обновлен"
        } catch {
            statusText = "Ошибка статуса сервисов: \(error.localizedDescription)"
        }
    }

    private func ensureServices() async {
        statusText = "Поднимаю сервисы..."
        do {
            let status = try await api.servicesEnsure()
            summarizeServices(status)
            statusText = status.ok ? "Сервисы запущены/проверены" : "Не удалось поднять сервисы"
        } catch {
            statusText = "Ошибка запуска сервисов: \(error.localizedDescription)"
        }
    }

    private func restartServices() async {
        statusText = "Перезапуск сервисов..."
        do {
            let status = try await api.servicesRestart()
            summarizeServices(status)
            statusText = status.ok ? "Сервисы перезапущены" : "Перезапуск завершился с ошибкой"
        } catch {
            statusText = "Ошибка перезапуска сервисов: \(error.localizedDescription)"
        }
    }
}
