import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    private enum SystemHealthState {
        case good
        case bad
    }

    @StateObject private var api = APIClient()
    @State private var statusText = "Готово"
    @State private var dashboardURL = ""
    @State private var latestInfo = ""
    @State private var dashboardLink: URL?
    @State private var isUpdatingLaw = false
    @State private var servicesInfo = ""
    @State private var isAutoRecovering = false
    @State private var healthState: SystemHealthState = .bad
    @State private var lastHealthCheckText = "—"
    @State private var directorMessages: [DirectorMessage] = []
    @State private var directorInput = ""
    @State private var directorNote = ""
    @State private var isDirectorBusy = false
    @State private var isFileImporterPresented = false

    var body: some View {
        NavigationView {
            Form {
                Section("Состояние системы") {
                    HStack {
                        Spacer()
                        VStack(spacing: 10) {
                            Circle()
                                .fill(healthState == .good ? Color.green : Color.red)
                                .frame(width: 84, height: 84)
                                .overlay(
                                    Circle()
                                        .stroke(Color.primary.opacity(0.1), lineWidth: 1)
                                )

                            Text(healthState == .good ? "ЗЕЛЕНЫЙ" : "КРАСНЫЙ")
                                .font(.headline)
                                .fontWeight(.semibold)
                        }
                        Spacer()
                    }
                    Text("Последняя проверка: \(lastHealthCheckText)")
                        .font(.footnote)
                }

                Section("Директор (AI)") {
                    if directorMessages.isEmpty {
                        Text("Диалог пока пуст. Отправьте задачу директору.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    } else {
                        ScrollView {
                            VStack(spacing: 8) {
                                ForEach(directorMessages.suffix(8)) { message in
                                    HStack {
                                        if message.role == "assistant" {
                                            directorBubble(
                                                text: message.content,
                                                isAssistant: true
                                            )
                                            Spacer(minLength: 20)
                                        } else {
                                            Spacer(minLength: 20)
                                            directorBubble(
                                                text: message.content,
                                                isAssistant: false
                                            )
                                        }
                                    }
                                }
                            }
                            .padding(.vertical, 4)
                        }
                        .frame(minHeight: 120, maxHeight: 260)
                    }

                    TextField("Поручение директору", text: $directorInput, axis: .vertical)
                        .lineLimit(2...5)
                        .textInputAutocapitalization(.never)
                    Button("Отправить директору") {
                        Task {
                            await sendDirectorMessage()
                        }
                    }
                    .disabled(isDirectorBusy || directorInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

                    TextField("Комментарий к документу (опц.)", text: $directorNote)
                        .textInputAutocapitalization(.never)
                    Button("Загрузить документ директору") {
                        isFileImporterPresented = true
                    }
                    .disabled(isDirectorBusy)
                }

                Section("Подключение") {
                    TextField("API URL", text: $api.baseURL)
                        .textInputAutocapitalization(.never)
                        .disableAutocorrection(true)
                    Button("Автоисправление (1 кнопка)") {
                        Task {
                            await autoRecover()
                        }
                    }
                    .disabled(isAutoRecovering)
                    Button("Сбросить URL на авто (LAN)") {
                        Task {
                            await autoRecover()
                        }
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
                await loadServicesStatus()
                await loadDirectorHistory()
                await startHealthAutoRefresh()
            }
            .fileImporter(
                isPresented: $isFileImporterPresented,
                allowedContentTypes: [.pdf, .plainText, .rtf, .spreadsheet, .item],
                allowsMultipleSelection: false
            ) { result in
                switch result {
                case .success(let urls):
                    guard let url = urls.first else { return }
                    Task {
                        await uploadDirectorDocument(from: url)
                    }
                case .failure(let error):
                    statusText = "Ошибка выбора файла: \(error.localizedDescription)"
                }
            }
        }
    }

    private func checkHealth() async {
        do {
            let response = try await api.health()
            statusText = response.ok ? "API онлайн: \(response.service)" : "API недоступен"
            if response.ok {
                healthState = .good
            }
        } catch {
            statusText = "Нет связи с API. Нажмите 'Поднять сервисы' в разделе Сервисы."
            healthState = .bad
        }
        lastHealthCheckText = nowText()
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
        healthState = (s.api_process && s.bot_process && s.api_health) ? .good : .bad
        lastHealthCheckText = nowText()
    }

    private func loadServicesStatus() async {
        do {
            let status = try await api.servicesStatus()
            summarizeServices(status)
            statusText = "Статус сервисов обновлен"
        } catch {
            statusText = "Ошибка статуса сервисов: \(error.localizedDescription)"
            healthState = .bad
            lastHealthCheckText = nowText()
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

    private func autoRecover() async {
        isAutoRecovering = true
        statusText = "Автоподключение и восстановление сервисов..."
        do {
            let result = try await api.autoConnectAndEnsureServices()
            summarizeServices(result.status)
            if result.discoveredOnLAN {
                statusText = "Готово: API найден в LAN (\(result.baseURL)), сервисы проверены"
            } else {
                statusText = "Готово: подключение к \(result.baseURL), сервисы проверены"
            }
        } catch {
            statusText = "Автовосстановление не удалось: \(error.localizedDescription)"
        }
        isAutoRecovering = false
    }

    private func startHealthAutoRefresh() async {
        while !Task.isCancelled {
            try? await Task.sleep(nanoseconds: 10_000_000_000)
            if Task.isCancelled {
                return
            }
            await loadServicesStatus()
        }
    }

    private func nowText() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ru_RU")
        formatter.dateFormat = "dd.MM.yyyy HH:mm:ss"
        return formatter.string(from: Date())
    }

    private func loadDirectorHistory() async {
        do {
            let response = try await api.directorHistory()
            directorMessages = response.messages
        } catch {
            statusText = "Ошибка загрузки диалога директора: \(error.localizedDescription)"
        }
    }

    private func sendDirectorMessage() async {
        let text = directorInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        isDirectorBusy = true
        statusText = "Директор анализирует задачу..."
        do {
            let response = try await api.directorSend(text: text)
            if let messages = response.messages {
                directorMessages = messages
            } else {
                await loadDirectorHistory()
            }
            directorInput = ""
            statusText = "Ответ директора получен"
        } catch {
            statusText = "Ошибка чата директора: \(error.localizedDescription)"
        }
        isDirectorBusy = false
    }

    private func uploadDirectorDocument(from url: URL) async {
        isDirectorBusy = true
        statusText = "Загружаю документ директору..."
        let hasScope = url.startAccessingSecurityScopedResource()
        defer {
            if hasScope {
                url.stopAccessingSecurityScopedResource()
            }
        }

        do {
            let data = try Data(contentsOf: url)
            let name = url.lastPathComponent
            let mime = mimeType(for: url)
            let response = try await api.directorUpload(
                filename: name,
                mimeType: mime,
                fileData: data,
                note: directorNote
            )
            if let messages = response.messages {
                directorMessages = messages
            } else {
                await loadDirectorHistory()
            }
            directorNote = ""
            statusText = "Документ передан директору"
        } catch {
            statusText = "Ошибка загрузки документа: \(error.localizedDescription)"
        }
        isDirectorBusy = false
    }

    private func mimeType(for url: URL) -> String {
        if let type = UTType(filenameExtension: url.pathExtension),
           let mime = type.preferredMIMEType {
            return mime
        }
        return "application/octet-stream"
    }

    @ViewBuilder
    private func directorBubble(text: String, isAssistant: Bool) -> some View {
        Text(text)
            .font(.system(.footnote, design: .rounded))
            .foregroundStyle(isAssistant ? Color.primary : Color.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 14, style: .continuous)
                    .fill(isAssistant ? Color(.secondarySystemBackground) : Color.blue)
            )
    }
}
