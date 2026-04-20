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
            ScrollView {
                VStack(spacing: 14) {
                    healthCard
                    directorCard
                    actionsCard
                    legalCard
                    statusCard
                }
                .padding(14)
            }
            .background(backgroundView)
            .navigationTitle("StroyStandart Office")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    settingsMenu
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    statusDot
                }
            }
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

    private var backgroundView: some View {
        LinearGradient(
            colors: [Color(red: 0.95, green: 0.97, blue: 1.0), Color(red: 0.98, green: 0.99, blue: 1.0)],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }

    private var settingsMenu: some View {
        Menu {
            Button("Автоисправление") {
                Task { await autoRecover() }
            }
            Button("Проверить соединение") {
                Task {
                    await checkHealth()
                    await loadServicesStatus()
                }
            }
            Button("URL: localhost") {
                api.baseURL = "http://127.0.0.1:8787"
                statusText = "URL переключен на localhost"
            }
            Button("URL: авто LAN") {
                Task { await autoRecover() }
            }
            Button("Обновить юр. источники") {
                Task { await runLawUpdate() }
            }
            if let dashboardLink {
                Link("Открыть дашборд", destination: dashboardLink)
            }
        } label: {
            Label("Настройки", systemImage: "slider.horizontal.3")
                .labelStyle(.iconOnly)
                .font(.title3)
        }
    }

    private var statusDot: some View {
        Circle()
            .fill(healthState == .good ? Color.green : Color.red)
            .frame(width: 11, height: 11)
            .overlay(Circle().stroke(Color.white.opacity(0.7), lineWidth: 1))
    }

    private var healthCard: some View {
        card {
            HStack(spacing: 10) {
                statusDot
                VStack(alignment: .leading, spacing: 4) {
                    Text(healthState == .good ? "Система в норме" : "Требуется внимание")
                        .font(.headline)
                    Text("Последняя проверка: \(lastHealthCheckText)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }
        }
    }

    private var directorCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack(spacing: 10) {
                    Circle()
                        .fill(LinearGradient(colors: [Color.black, Color.blue], startPoint: .topLeading, endPoint: .bottomTrailing))
                        .frame(width: 34, height: 34)
                        .overlay(Text("ЭК").font(.caption2).fontWeight(.bold).foregroundStyle(.white))
                    VStack(alignment: .leading, spacing: 1) {
                        Text("Эмилио Ковальский")
                            .font(.headline)
                        Text("Исполнительный директор AI")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if isDirectorBusy {
                        ProgressView()
                            .scaleEffect(0.85)
                    }
                }

                if directorMessages.isEmpty {
                    Text("Диалог пуст. Дайте задачу директору или загрузите документ.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .padding(.vertical, 8)
                } else {
                    ScrollView {
                        VStack(spacing: 8) {
                            ForEach(directorMessages.suffix(10)) { message in
                                HStack {
                                    if message.role == "assistant" {
                                        directorBubble(message: message, isAssistant: true)
                                        Spacer(minLength: 16)
                                    } else {
                                        Spacer(minLength: 16)
                                        directorBubble(message: message, isAssistant: false)
                                    }
                                }
                            }
                        }
                        .padding(.vertical, 4)
                    }
                    .frame(minHeight: 120, maxHeight: 280)
                }

                VStack(spacing: 8) {
                    TextField("Напишите поручение директору", text: $directorInput, axis: .vertical)
                        .lineLimit(2...5)
                        .padding(10)
                        .background(Color.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                    HStack(spacing: 8) {
                        Button {
                            Task { await sendDirectorMessage() }
                        } label: {
                            Label("Отправить", systemImage: "paperplane.fill")
                                .font(.subheadline.weight(.semibold))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                        }
                        .buttonStyle(.borderedProminent)
                        .disabled(isDirectorBusy || directorInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

                        Button {
                            isFileImporterPresented = true
                        } label: {
                            Label("Файл", systemImage: "paperclip")
                                .font(.subheadline.weight(.semibold))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                        }
                        .buttonStyle(.bordered)
                        .disabled(isDirectorBusy)
                    }

                    TextField("Комментарий к загружаемому документу", text: $directorNote)
                        .textInputAutocapitalization(.never)
                        .padding(10)
                        .background(Color.white)
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                }
            }
        }
    }

    private var actionsCard: some View {
        card {
            VStack(alignment: .leading, spacing: 10) {
                Text("Операции")
                    .font(.headline)

                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                    actionButton("Автоисправление", "wand.and.stars") { await autoRecover() }
                    actionButton("Статус сервисов", "waveform.path.ecg") { await loadServicesStatus() }
                    actionButton("Поднять сервисы", "bolt.fill") { await ensureServices() }
                    actionButton("Перезапуск", "arrow.clockwise") { await restartServices() }
                }

                if !servicesInfo.isEmpty {
                    Text(servicesInfo)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }

    private var legalCard: some View {
        card {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Юридический блок")
                        .font(.headline)
                    Spacer()
                    if isUpdatingLaw {
                        ProgressView()
                            .scaleEffect(0.8)
                    }
                }

                HStack(spacing: 8) {
                    Button("Обновить") {
                        Task { await runLawUpdate() }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(isUpdatingLaw)

                    Button("Последний отчет") {
                        Task { await loadLatestLawReport() }
                    }
                    .buttonStyle(.bordered)

                    Button("Дашборд") {
                        Task { await fetchDashboard() }
                    }
                    .buttonStyle(.bordered)
                }

                if !latestInfo.isEmpty {
                    Text(latestInfo)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if let dashboardLink {
                    Link("Открыть дашборд", destination: dashboardLink)
                        .font(.caption)
                }
            }
        }
    }

    private var statusCard: some View {
        card {
            VStack(alignment: .leading, spacing: 6) {
                Text("Статус")
                    .font(.headline)
                Text(statusText)
                    .font(.footnote)
                Text("API: \(api.baseURL)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
                    .truncationMode(.middle)
            }
        }
    }

    private func card<Content: View>(@ViewBuilder _ content: () -> Content) -> some View {
        content()
            .padding(12)
            .background(.ultraThinMaterial)
            .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(Color.black.opacity(0.05), lineWidth: 1)
            )
    }

    private func actionButton(_ title: String, _ icon: String, action: @escaping () async -> Void) -> some View {
        Button {
            Task { await action() }
        } label: {
            Label(title, systemImage: icon)
                .font(.caption.weight(.semibold))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 10)
        }
        .buttonStyle(.bordered)
    }

    @ViewBuilder
    private func directorBubble(message: DirectorMessage, isAssistant: Bool) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(message.content)
                .font(.system(.footnote, design: .rounded))
                .foregroundStyle(isAssistant ? Color.primary : Color.white)
            if let createdAt = message.created_at, !createdAt.isEmpty {
                Text(createdAt.replacingOccurrences(of: "T", with: " "))
                    .font(.caption2)
                    .foregroundStyle(isAssistant ? Color.secondary : Color.white.opacity(0.75))
            }
        }
        .padding(.horizontal, 11)
        .padding(.vertical, 8)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(Color.white)
                .overlay(
                    RoundedRectangle(cornerRadius: 14, style: .continuous)
                        .fill(
                            LinearGradient(
                                colors: [Color.blue, Color.indigo],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .opacity(isAssistant ? 0 : 1)
                )
        )
    }

    private func checkHealth() async {
        do {
            let response = try await api.health()
            statusText = response.ok ? "API онлайн: \(response.service)" : "API недоступен"
            healthState = response.ok ? .good : .bad
        } catch {
            statusText = "Нет связи с API. Нажмите Автоисправление."
            healthState = .bad
        }
        lastHealthCheckText = nowText()
    }

    private func fetchDashboard() async {
        do {
            let response = try await api.dashboard()
            dashboardURL = response.dashboard_url
            dashboardLink = URL(string: dashboardURL.trimmingCharacters(in: .whitespacesAndNewlines))
            statusText = dashboardLink == nil ? "Dashboard пока недоступен" : "Ссылка дашборда загружена"
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
        statusText = "Обновление запущено..."
        do {
            let response = try await api.lawUpdate()
            if response.ok, response.running == true {
                statusText = "Идет обновление..."
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
        statusText = "Обновление занимает много времени. Проверьте позже."
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
        statusText = "Автоподключение и восстановление..."
        do {
            let result = try await api.autoConnectAndEnsureServices()
            summarizeServices(result.status)
            if result.discoveredOnLAN {
                statusText = "Готово: API найден в LAN (\(result.baseURL))"
            } else {
                statusText = "Готово: подключение к \(result.baseURL)"
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
}
