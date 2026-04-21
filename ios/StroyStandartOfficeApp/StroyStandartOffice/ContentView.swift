import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    private enum SystemHealthState {
        case good
        case bad
    }

    private enum WorkspaceSection: String, CaseIterable, Identifiable {
        case overview = "Обзор"
        case inbox = "Входящие"
        case documents = "Документы"

        var id: String { rawValue }

        var icon: String {
            switch self {
            case .overview: return "sparkles.rectangle.stack"
            case .inbox: return "tray.full"
            case .documents: return "doc.text"
            }
        }
    }

    private struct DirectorTask: Codable, Identifiable, Equatable {
        struct Event: Codable, Identifiable, Equatable {
            let id: String
            let title: String
            let detail: String
            let createdAt: String
            let tint: String
        }

        enum Priority: String, Codable, CaseIterable {
            case high = "Высокий"
            case medium = "Средний"
            case low = "Низкий"

            var color: Color {
                switch self {
                case .high: return .red
                case .medium: return .orange
                case .low: return .green
                }
            }
        }

        enum Stage: String, Codable, CaseIterable {
            case new = "К исполнению"
            case inProgress = "В работе"
            case control = "На контроле"

            var color: Color {
                switch self {
                case .new: return .blue
                case .inProgress: return .orange
                case .control: return .purple
                }
            }
        }

        let id: String
        var title: String
        var detail: String
        var createdAt: String
        var dueAt: String?
        var priority: Priority
        var assignee: String
        var stage: Stage
        var completedAt: String?
        var timeline: [Event]
        var unreadAlerts: Int

        var isCompleted: Bool {
            completedAt != nil
        }

        init(
            id: String,
            title: String,
            detail: String,
            createdAt: String,
            dueAt: String?,
            priority: Priority,
            assignee: String,
            stage: Stage,
            completedAt: String?,
            timeline: [Event] = [],
            unreadAlerts: Int = 0
        ) {
            self.id = id
            self.title = title
            self.detail = detail
            self.createdAt = createdAt
            self.dueAt = dueAt
            self.priority = priority
            self.assignee = assignee
            self.stage = stage
            self.completedAt = completedAt
            self.timeline = timeline
            self.unreadAlerts = unreadAlerts
        }

        enum CodingKeys: String, CodingKey {
            case id, title, detail, createdAt, dueAt, priority, assignee, stage, completedAt, timeline, unreadAlerts
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            id = try container.decode(String.self, forKey: .id)
            title = try container.decode(String.self, forKey: .title)
            detail = try container.decode(String.self, forKey: .detail)
            createdAt = try container.decode(String.self, forKey: .createdAt)
            dueAt = try container.decodeIfPresent(String.self, forKey: .dueAt)
            priority = try container.decode(Priority.self, forKey: .priority)
            assignee = try container.decode(String.self, forKey: .assignee)
            stage = try container.decode(Stage.self, forKey: .stage)
            completedAt = try container.decodeIfPresent(String.self, forKey: .completedAt)
            timeline = try container.decodeIfPresent([Event].self, forKey: .timeline) ?? []
            unreadAlerts = try container.decodeIfPresent(Int.self, forKey: .unreadAlerts) ?? 0
        }
    }

    private struct ExecutionSnapshot: Identifiable {
        let id: String
        let executor: String
        let workerRole: String
        let status: String
        let resultSummary: String
        let nextStep: String
        let resolution: String
        let needsRevision: Bool
        let createdAt: String?
        let revisionComments: String
    }

    private enum TaskRoleFilter: String, CaseIterable, Identifiable {
        case all = "Все"
        case director = "Директор"
        case legal = "Юрист"
        case pto = "ПТО"
        case finance = "Финансы"
        case supply = "Снабжение"

        var id: String { rawValue }
    }

    private struct ExecutorHistoryTarget: Identifiable {
        let id: String
        let name: String
    }

    @StateObject private var api = APIClient()
    @AppStorage("ui_dark_mode") private var useDarkMode = true
    @AppStorage("director_tasks_json") private var directorTasksJSON = "[]"
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
    @State private var showLastCheckToast = false
    @State private var isChatInteracting = false
    @State private var selectedSection: WorkspaceSection = .overview
    @State private var isDirectorWorkspacePresented = false
    @State private var lastUploadedFileName = ""
    @State private var directorTasks: [DirectorTask] = []
    @State private var selectedTaskID: String?
    @State private var selectedTaskRoleFilter: TaskRoleFilter = .all
    @State private var selectedExecutorHistory: ExecutorHistoryTarget?
    @FocusState private var isDirectorInputFocused: Bool
    @FocusState private var isDirectorNoteFocused: Bool

    var body: some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 14) {
                    workspaceSwitcher

                    switch selectedSection {
                    case .overview:
                        directorSummaryCard
                        directorAlertsCard
                        executionControlCard
                        executorHistoryCard
                        directorTaskBoardCard
                        executionInboxCard
                        statusCard
                    case .inbox:
                        executionInboxCard
                        inboxCard
                        directorTaskBoardCard
                    case .documents:
                        documentCard
                        documentWorkflowCard
                        directorTaskBoardCard
                        statusCard
                    }
                }
                .padding(14)
            }
            .scrollDisabled(isChatInteracting)
            .background(backgroundView)
            .preferredColorScheme(useDarkMode ? .dark : .light)
            .navigationTitle("StroyStandart Office")
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    settingsMenu
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    statusDot
                }
            }
            .overlay(alignment: .topTrailing) {
                if showLastCheckToast {
                    Text("Последняя проверка: \(lastHealthCheckText)")
                        .font(.caption.weight(.semibold))
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(.ultraThinMaterial)
                        .clipShape(Capsule())
                        .padding(.top, 6)
                        .padding(.trailing, 14)
                        .transition(.opacity.combined(with: .move(edge: .top)))
                }
            }
            .task {
                loadDirectorTasks()
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
            .sheet(isPresented: $isDirectorWorkspacePresented) {
                directorWorkspaceSheet
            }
            .sheet(item: selectedTaskBinding) { task in
                directorTaskDetailSheet(task: task)
            }
            .sheet(item: $selectedExecutorHistory) { executor in
                executorHistorySheet(executor: executor.name)
            }
        }
    }

    private var backgroundView: some View {
        Group {
            if useDarkMode {
                LinearGradient(
                    colors: [Color(red: 0.06, green: 0.09, blue: 0.14), Color(red: 0.10, green: 0.12, blue: 0.18)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            } else {
                LinearGradient(
                    colors: [Color(red: 0.95, green: 0.97, blue: 1.0), Color(red: 0.98, green: 0.99, blue: 1.0)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            }
        }
        .ignoresSafeArea()
    }

    private var settingsMenu: some View {
        Menu {
            Button(useDarkMode ? "Светлая тема" : "Тёмная тема") {
                useDarkMode.toggle()
            }
            Button("Открыть директора") {
                isDirectorWorkspacePresented = true
            }
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
            Menu("Скрытые разделы") {
                Button("Статус сервисов") {
                    Task { await loadServicesStatus() }
                }
                Button("Поднять сервисы") {
                    Task { await ensureServices() }
                }
                Button("Перезапустить сервисы") {
                    Task { await restartServices() }
                }
                Button("Обновить юр. источники") {
                    Task { await runLawUpdate() }
                }
                Button("Последний юр. отчет") {
                    Task { await loadLatestLawReport() }
                }
                Button("Обновить ссылку дашборда") {
                    Task { await fetchDashboard() }
                }
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

    private var workspaceSwitcher: some View {
        card {
            VStack(alignment: .leading, spacing: 10) {
                HStack {
                    Text("Рабочее пространство")
                        .font(.headline)
                    Spacer()
                    Button("Открыть чат") {
                        isDirectorWorkspacePresented = true
                    }
                    .font(.caption.weight(.semibold))
                }

                HStack(spacing: 8) {
                    ForEach(WorkspaceSection.allCases) { section in
                        Button {
                            withAnimation(.spring(response: 0.28, dampingFraction: 0.9)) {
                                selectedSection = section
                            }
                        } label: {
                            Label(section.rawValue, systemImage: section.icon)
                                .font(.caption.weight(.semibold))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 10)
                                .background(
                                    RoundedRectangle(cornerRadius: 12, style: .continuous)
                                        .fill(selectedSection == section ? Color.accentColor.opacity(0.18) : Color.clear)
                                )
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }

    private var statusDot: some View {
        Circle()
            .fill(healthState == .good ? Color.green : Color.red)
            .frame(width: 11, height: 11)
            .overlay(Circle().stroke(Color.white.opacity(0.7), lineWidth: 1))
            .contentShape(Rectangle())
            .padding(.vertical, 6)
            .onLongPressGesture(minimumDuration: 5) {
                withAnimation(.easeInOut(duration: 0.2)) {
                    showLastCheckToast = true
                }
                DispatchQueue.main.asyncAfter(deadline: .now() + 4) {
                    withAnimation(.easeInOut(duration: 0.2)) {
                        showLastCheckToast = false
                    }
                }
            }
    }

    private var healthCard: some View {
        card {
            HStack(spacing: 10) {
                Image(systemName: "building.2.crop.circle")
                    .font(.title3)
                    .foregroundStyle(.indigo)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Командный центр")
                        .font(.headline)
                    Text("Статус смотри по кружку справа вверху")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
            }
        }
    }

    private var directorSummaryCard: some View {
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

                Text("Поручения, ответы и загрузка документов теперь доступны в отдельном рабочем окне директора.")
                    .font(.footnote)
                    .foregroundStyle(.secondary)

                HStack(spacing: 10) {
                    statCapsule(title: "Сообщений", value: "\(directorMessages.count)")
                    statCapsule(title: "Ответов", value: "\(assistantMessages.count)")
                    statCapsule(title: "Задач", value: "\(activeDirectorTasks.count)")
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                HStack(spacing: 10) {
                    statCapsule(title: "Просрочено", value: "\(overdueDirectorTasks.count)")
                    statCapsule(title: "Исполнено", value: "\(completedDirectorTasks.count)")
                    statCapsule(title: "В работе", value: "\(tasksInProgress.count)")
                }
                .frame(maxWidth: .infinity, alignment: .leading)

                if unreadAlertTasksCount > 0 {
                    HStack(spacing: 8) {
                        Image(systemName: "bell.badge.fill")
                            .foregroundStyle(.orange)
                        Text("Есть новые сигналы директора: \(unreadAlertTasksCount)")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.orange)
                    }
                    .padding(10)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.orange.opacity(0.10))
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                }

                if let lastAssistant = assistantMessages.last {
                    VStack(alignment: .leading, spacing: 6) {
                        Text("Последняя резолюция")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(.secondary)
                        directorBubble(message: lastAssistant, isAssistant: true)
                    }
                }

                HStack(spacing: 8) {
                    Button {
                        isDirectorWorkspacePresented = true
                    } label: {
                        Label("Открыть диалог", systemImage: "message.fill")
                            .font(.subheadline.weight(.semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                    }
                    .buttonStyle(.borderedProminent)

                    Button {
                        isFileImporterPresented = true
                    } label: {
                        Label("Загрузить файл", systemImage: "paperclip")
                            .font(.subheadline.weight(.semibold))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 10)
                    }
                    .buttonStyle(.bordered)
                    .disabled(isDirectorBusy)
                }
            }
        }
    }

    private var directorAlertsCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Сигналы директора")
                            .font(.headline)
                        Text("Новые возвраты и замечания к задачам")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if unreadAlertTasksCount > 0 {
                        taskMetaChip(text: "\(unreadAlertTasksCount)", tint: .orange)
                    }
                }

                if alertTasks.isEmpty {
                    taskPlaceholder("Новых возвратов на доработку пока нет.")
                } else {
                    VStack(spacing: 8) {
                        ForEach(alertTasks.prefix(3)) { task in
                            Button {
                                selectedTaskID = task.id
                                markTaskAlertsRead(task.id)
                            } label: {
                                HStack(alignment: .top, spacing: 10) {
                                    Circle()
                                        .fill(Color.orange.opacity(0.18))
                                        .frame(width: 30, height: 30)
                                        .overlay(Image(systemName: "bell.badge.fill").foregroundStyle(.orange))
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(task.title)
                                            .font(.footnote.weight(.semibold))
                                        Text(latestRevisionText(for: task) ?? "Есть новое замечание директора")
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                            .lineLimit(2)
                                    }
                                    Spacer()
                                    Text("\(task.unreadAlerts)")
                                        .font(.caption.weight(.bold))
                                        .foregroundStyle(.orange)
                                }
                                .padding(10)
                                .background(Color.orange.opacity(0.10))
                                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }
        }
    }

    private var directorTaskBoardCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Задачи директора")
                            .font(.headline)
                        Text("Текущие поручения и исполненный контур")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button("Открыть чат") {
                        isDirectorWorkspacePresented = true
                    }
                    .font(.caption.weight(.semibold))
                }

                VStack(alignment: .leading, spacing: 8) {
                    Text("Текущие задачи директора")
                        .font(.subheadline.weight(.semibold))

                    taskRoleFilterStrip

                    if filteredActiveDirectorTasks.isEmpty {
                        taskPlaceholder("Активных задач пока нет. Отправь директору поручение, и оно появится здесь автоматически.")
                    } else {
                        if !overdueDirectorTasks.isEmpty {
                            HStack(spacing: 8) {
                                Image(systemName: "exclamationmark.triangle.fill")
                                    .foregroundStyle(.red)
                                Text("Есть просроченные задачи: \(overdueDirectorTasks.count)")
                                    .font(.caption.weight(.semibold))
                                    .foregroundStyle(.red)
                            }
                            .padding(10)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color.red.opacity(0.08))
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        }
                        ForEach(filteredActiveDirectorTasks) { task in
                            directorTaskRow(task: task, completed: false)
                        }
                    }
                }

                Divider()

                VStack(alignment: .leading, spacing: 8) {
                    Text("Исполненные задачи")
                        .font(.subheadline.weight(.semibold))

                    if filteredCompletedDirectorTasks.isEmpty {
                        taskPlaceholder("Закрытые задачи будут собираться здесь.")
                    } else {
                        ForEach(filteredCompletedDirectorTasks.prefix(5)) { task in
                            directorTaskRow(task: task, completed: true)
                        }
                    }
                }
            }
        }
    }

    private var executionControlCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Исполнительский контур")
                            .font(.headline)
                        Text("Кто сейчас работает под директором")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if let latest = executionSnapshots.first {
                        taskMetaChip(text: latest.status, tint: latest.needsRevision ? .orange : .green)
                    }
                }

                HStack(spacing: 8) {
                    roleLoadCapsule(title: "Юрист", value: "\(taskCount(for: "Юрист"))", tint: .indigo, executor: "Юрист")
                    roleLoadCapsule(title: "ПТО", value: "\(taskCount(for: "ПТО"))", tint: .teal, executor: "ПТО")
                    roleLoadCapsule(title: "Финансы", value: "\(taskCount(for: "Финансы"))", tint: .orange, executor: "Финансы")
                    roleLoadCapsule(title: "Директор", value: "\(taskCount(for: "Директор"))", tint: .blue, executor: "Директор")
                }

                if let latest = executionSnapshots.first {
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Последний исполнитель")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(.secondary)
                            Spacer()
                            if let createdAt = latest.createdAt, !createdAt.isEmpty {
                                Text(createdAt.replacingOccurrences(of: "T", with: " "))
                                    .font(.caption2)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        executionHighlightCard(latest)
                        if latest.needsRevision, !latest.revisionComments.isEmpty {
                            revisionFeedbackCard(latest)
                        }
                    }
                } else {
                    taskPlaceholder("После ответа директора здесь появится карточка исполнителя с результатом и следующим шагом.")
                }
            }
        }
    }

    private var executorHistoryCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("История исполнителей")
                            .font(.headline)
                        Text("Последние принятые и возвращенные результаты по ролям")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                }

                if topExecutors.isEmpty {
                    taskPlaceholder("Когда подчиненные начнут закрывать задачи, здесь появится их история.")
                } else {
                    VStack(spacing: 8) {
                        ForEach(topExecutors, id: \.self) { executor in
                            Button {
                                selectedExecutorHistory = ExecutorHistoryTarget(id: executor, name: executor)
                            } label: {
                                HStack(spacing: 10) {
                                    Circle()
                                        .fill(executorTint(executor).opacity(0.18))
                                        .frame(width: 30, height: 30)
                                        .overlay(Image(systemName: "person.text.rectangle.fill").foregroundStyle(executorTint(executor)))
                                    VStack(alignment: .leading, spacing: 4) {
                                        Text(executor)
                                            .font(.footnote.weight(.semibold))
                                        Text(executorHistorySubtitle(executor))
                                            .font(.caption)
                                            .foregroundStyle(.secondary)
                                            .lineLimit(2)
                                    }
                                    Spacer()
                                    Image(systemName: "chevron.right")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                .padding(10)
                                .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
                                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
            }
        }
    }

    private var inboxCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Входящие директора")
                            .font(.headline)
                        Text("Последние ответы и рабочие сигналы")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button("Все") {
                        isDirectorWorkspacePresented = true
                    }
                    .font(.caption.weight(.semibold))
                }

                if assistantMessages.isEmpty {
                    Text("Пока нет ответов директора. Отправьте задачу или загрузите документ.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                } else {
                    VStack(spacing: 8) {
                        ForEach(Array(assistantMessages.suffix(3).reversed())) { message in
                            HStack(alignment: .top, spacing: 10) {
                                Circle()
                                    .fill(Color.accentColor.opacity(0.18))
                                    .frame(width: 28, height: 28)
                                    .overlay(Image(systemName: "person.crop.square").font(.caption))
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(message.content)
                                        .font(.footnote)
                                        .lineLimit(3)
                                    if let createdAt = message.created_at, !createdAt.isEmpty {
                                        Text(createdAt.replacingOccurrences(of: "T", with: " "))
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                Spacer()
                            }
                            .padding(10)
                            .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                        }
                    }
                }
            }
        }
    }

    private var executionInboxCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Результаты исполнителей")
                            .font(.headline)
                        Text("Юрист, ПТО, финансы и директорская проверка")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Button("Чат") {
                        isDirectorWorkspacePresented = true
                    }
                    .font(.caption.weight(.semibold))
                }

                if executionSnapshots.isEmpty {
                    taskPlaceholder("Когда подчиненный выполнит задачу, здесь появится его карточка с итогом проверки директора.")
                } else {
                    VStack(spacing: 8) {
                        ForEach(executionSnapshots.prefix(4)) { snapshot in
                            executionInboxRow(snapshot)
                        }
                    }
                }
            }
        }
    }

    private var documentCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Документы")
                            .font(.headline)
                        Text("Передача директору и быстрые шаблоны")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Image(systemName: "folder.badge.plus")
                        .font(.title3)
                        .foregroundStyle(Color.accentColor)
                }

                HStack(spacing: 8) {
                    quickPromptButton("Согласовать договор") {
                        directorInput = "Проверь и согласуй договор. Дай резолюцию, риски и следующий шаг."
                        isDirectorWorkspacePresented = true
                    }
                    quickPromptButton("Проверить письмо") {
                        directorInput = "Проверь исходящее письмо. Дай правки, тон и финальную резолюцию."
                        isDirectorWorkspacePresented = true
                    }
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text("Последняя загрузка")
                        .font(.caption.weight(.semibold))
                        .foregroundStyle(.secondary)
                    Text(lastUploadedFileName.isEmpty ? "Файлы еще не передавались директору." : lastUploadedFileName)
                        .font(.footnote)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(10)
                .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

                TextField("Комментарий к документу", text: $directorNote)
                    .textInputAutocapitalization(.never)
                    .padding(10)
                    .background(Color(.secondarySystemBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))

                Button {
                    isFileImporterPresented = true
                } label: {
                    Label("Выбрать и загрузить документ", systemImage: "paperclip.circle.fill")
                        .font(.subheadline.weight(.semibold))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                }
                .buttonStyle(.borderedProminent)
                .disabled(isDirectorBusy)
            }
        }
    }

    private var documentWorkflowCard: some View {
        card {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Документный контур")
                            .font(.headline)
                        Text("Текущие документы в работе у директора")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    taskMetaChip(text: "\(documentTasks.count)", tint: .blue)
                }

                if documentTasks.isEmpty {
                    taskPlaceholder("После загрузки файла здесь появится его рабочий путь и статус.")
                } else {
                    VStack(spacing: 8) {
                        ForEach(documentTasks.prefix(4)) { task in
                            Button {
                                selectedTaskID = task.id
                            } label: {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack {
                                        Text(task.title.replacingOccurrences(of: "Проверить документ: ", with: ""))
                                            .font(.footnote.weight(.semibold))
                                        Spacer()
                                        taskMetaChip(text: task.stage.rawValue, tint: task.stage.color)
                                    }
                                    Text(documentStatusText(for: task))
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(2)
                                    if let lastEvent = task.timeline.last {
                                        Text("Последнее событие: \(lastEvent.title)")
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)
                                    }
                                }
                                .frame(maxWidth: .infinity, alignment: .leading)
                                .padding(10)
                                .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
                                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            }
                            .buttonStyle(.plain)
                        }
                    }
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

    private var directorWorkspaceSheet: some View {
        NavigationView {
            VStack(spacing: 0) {
                directorWorkspaceHeader
                Divider()
                directorConversation(maxHeight: .infinity)
                Divider()
                directorComposer
            }
            .background(backgroundView)
            .preferredColorScheme(useDarkMode ? .dark : .light)
            .navigationTitle("Директор")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Закрыть") {
                        isDirectorInputFocused = false
                        isDirectorNoteFocused = false
                        isDirectorWorkspacePresented = false
                    }
                }
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Готово") {
                        isDirectorInputFocused = false
                        isDirectorNoteFocused = false
                    }
                }
            }
        }
    }

    private func directorTaskDetailSheet(task: DirectorTask) -> some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 14) {
                    card {
                        VStack(alignment: .leading, spacing: 12) {
                            HStack(alignment: .top) {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(task.title)
                                        .font(.title3.weight(.bold))
                                    Text(task.isCompleted ? "Исполненная задача" : "Активная задача директора")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                Circle()
                                    .fill(task.isCompleted ? Color.green.opacity(0.18) : task.priority.color.opacity(0.18))
                                    .frame(width: 42, height: 42)
                                    .overlay(
                                        Image(systemName: task.isCompleted ? "checkmark" : stageIcon(task.stage))
                                            .foregroundStyle(task.isCompleted ? .green : task.priority.color)
                                    )
                            }

                            if !task.detail.isEmpty {
                                Text(task.detail)
                                    .font(.body)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                                    .padding(12)
                                    .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
                                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            }

                            VStack(alignment: .leading, spacing: 10) {
                                detailRow(title: "Ответственный", value: task.assignee, tint: .teal)
                                detailRow(title: "Приоритет", value: task.priority.rawValue, tint: task.priority.color)
                                detailRow(title: "Стадия", value: task.isCompleted ? "Исполнено" : task.stage.rawValue, tint: task.isCompleted ? .green : task.stage.color)
                                detailRow(title: "Создано", value: task.createdAt, tint: .blue)
                                if let dueAt = task.dueAt, !dueAt.isEmpty {
                                    detailRow(title: "Срок", value: dueAt, tint: isTaskOverdue(task) ? .red : .indigo)
                                }
                                if let completedAt = task.completedAt, !completedAt.isEmpty {
                                    detailRow(title: "Закрыто", value: completedAt, tint: .green)
                                }
                            }
                        }
                    }

                    card {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Быстрые действия")
                                .font(.headline)

                            if !task.isCompleted {
                                HStack(spacing: 8) {
                                    Button {
                                        advanceTaskStage(task.id)
                                    } label: {
                                        Label("Сменить стадию", systemImage: stageIcon(task.stage))
                                            .frame(maxWidth: .infinity)
                                            .padding(.vertical, 10)
                                    }
                                    .buttonStyle(.bordered)

                                    Button {
                                        completeTask(task.id)
                                        selectedTaskID = task.id
                                    } label: {
                                        Label("Исполнено", systemImage: "checkmark.circle.fill")
                                            .frame(maxWidth: .infinity)
                                            .padding(.vertical, 10)
                                    }
                                    .buttonStyle(.borderedProminent)
                                }
                            } else {
                                Button {
                                    reopenTask(task.id)
                                    selectedTaskID = task.id
                                } label: {
                                    Label("Вернуть в работу", systemImage: "arrow.uturn.backward.circle")
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 10)
                                }
                                .buttonStyle(.bordered)
                            }
                        }
                    }

                    if let latestRevision = latestRevisionText(for: task), !latestRevision.isEmpty {
                        card {
                            VStack(alignment: .leading, spacing: 10) {
                                HStack(spacing: 8) {
                                    Image(systemName: "exclamationmark.bubble.fill")
                                        .foregroundStyle(.orange)
                                    Text("Последняя доработка")
                                        .font(.headline)
                                }
                                Text(latestRevision)
                                    .font(.footnote)
                                    .foregroundStyle(.secondary)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }
                        }
                    }

                    card {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Таймлайн задачи")
                                .font(.headline)

                            if task.timeline.isEmpty {
                                taskPlaceholder("История действий по задаче появится здесь.")
                            } else {
                                VStack(spacing: 10) {
                                    ForEach(task.timeline.reversed()) { event in
                                        taskTimelineRow(event)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(14)
            }
            .onAppear {
                markTaskAlertsRead(task.id)
            }
            .background(backgroundView)
            .preferredColorScheme(useDarkMode ? .dark : .light)
            .navigationTitle("Карточка задачи")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Закрыть") {
                        selectedTaskID = nil
                    }
                }
            }
        }
    }

    private func executorHistorySheet(executor: String) -> some View {
        NavigationView {
            ScrollView {
                VStack(spacing: 14) {
                    card {
                        VStack(alignment: .leading, spacing: 10) {
                            HStack {
                                Circle()
                                    .fill(executorTint(executor).opacity(0.18))
                                    .frame(width: 38, height: 38)
                                    .overlay(Image(systemName: "person.text.rectangle.fill").foregroundStyle(executorTint(executor)))
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(executor)
                                        .font(.headline)
                                    Text("История выполнения и директорских решений")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                            }
                            Text(executorHistorySubtitle(executor))
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                    }

                    card {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Последние задачи")
                                .font(.headline)

                            if executorTasks(executor).isEmpty {
                                taskPlaceholder("У этого исполнителя пока нет задач в истории.")
                            } else {
                                VStack(spacing: 10) {
                                    ForEach(executorTasks(executor).prefix(8)) { task in
                                        Button {
                                            selectedExecutorHistory = nil
                                            selectedTaskID = task.id
                                        } label: {
                                            VStack(alignment: .leading, spacing: 8) {
                                                HStack {
                                                    Text(task.title)
                                                        .font(.footnote.weight(.semibold))
                                                    Spacer()
                                                    taskMetaChip(text: task.isCompleted ? "Исполнено" : task.stage.rawValue, tint: task.isCompleted ? .green : task.stage.color)
                                                }
                                                Text(task.detail)
                                                    .font(.caption)
                                                    .foregroundStyle(.secondary)
                                                    .lineLimit(2)
                                                if let last = task.timeline.last {
                                                    Text("\(last.createdAt) • \(last.title)")
                                                        .font(.caption2)
                                                        .foregroundStyle(.secondary)
                                                }
                                            }
                                            .frame(maxWidth: .infinity, alignment: .leading)
                                            .padding(10)
                                            .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
                                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                                        }
                                        .buttonStyle(.plain)
                                    }
                                }
                            }
                        }
                    }
                }
                .padding(14)
            }
            .background(backgroundView)
            .preferredColorScheme(useDarkMode ? .dark : .light)
            .navigationTitle(executor)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Закрыть") {
                        selectedExecutorHistory = nil
                    }
                }
            }
        }
    }

    private var directorWorkspaceHeader: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(LinearGradient(colors: [Color.black, Color.blue], startPoint: .topLeading, endPoint: .bottomTrailing))
                .frame(width: 42, height: 42)
                .overlay(Text("ЭК").font(.caption).fontWeight(.bold).foregroundStyle(.white))
            VStack(alignment: .leading, spacing: 3) {
                Text("Эмилио Ковальский")
                    .font(.headline)
                Text("Управление, резолюции, документы")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            if isDirectorBusy {
                ProgressView()
            }
        }
        .padding(14)
    }

    private func directorConversation(maxHeight: CGFloat) -> some View {
        ScrollViewReader { proxy in
            ScrollView(.vertical, showsIndicators: true) {
                LazyVStack(spacing: 10) {
                    if directorMessages.isEmpty {
                        Text("Диалог пуст. Отправьте задачу, поручение или документ.")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .padding(.top, 18)
                    } else {
                        ForEach(directorMessages) { message in
                            HStack {
                                if message.role == "assistant" {
                                    directorBubble(message: message, isAssistant: true)
                                    Spacer(minLength: 20)
                                } else {
                                    Spacer(minLength: 20)
                                    directorBubble(message: message, isAssistant: false)
                                }
                            }
                        }
                    }
                    Color.clear
                        .frame(height: 1)
                        .id("director-chat-bottom")
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 12)
            }
            .frame(maxWidth: .infinity, maxHeight: maxHeight)
            .scrollIndicators(.visible)
            .scrollDismissesKeyboard(.interactively)
            .simultaneousGesture(
                TapGesture().onEnded {
                    isDirectorInputFocused = false
                    isDirectorNoteFocused = false
                }
            )
            .onAppear {
                proxy.scrollTo("director-chat-bottom", anchor: .bottom)
            }
            .onChange(of: directorMessages.count) { _ in
                withAnimation(.easeOut(duration: 0.2)) {
                    proxy.scrollTo("director-chat-bottom", anchor: .bottom)
                }
            }
        }
    }

    private var directorComposer: some View {
        VStack(spacing: 10) {
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 8) {
                    quickPromptButton("Срочно") {
                        directorInput = "Срочное поручение: подготовь решение, риски и контрольную точку сегодня."
                    }
                    quickPromptButton("Поручение") {
                        directorInput = "Поставь задачу по объекту, определи риск, срок и контрольную точку."
                    }
                    quickPromptButton("Отчет") {
                        directorInput = "Сформируй краткий отчет для директора: статус, риски, блокеры, следующий шаг."
                    }
                    quickPromptButton("Резолюция") {
                        directorInput = "Подготовь резолюцию по документу и решение по дальнейшим действиям."
                    }
                }
                .padding(.horizontal, 14)
            }

            TextField("Напишите поручение директору", text: $directorInput, axis: .vertical)
                .lineLimit(2...5)
                .padding(10)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .padding(.horizontal, 14)
                .focused($isDirectorInputFocused)

            HStack(spacing: 8) {
                Button {
                    addManualTaskFromInput()
                } label: {
                    Label("В задачу", systemImage: "plus.circle")
                        .font(.subheadline.weight(.semibold))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 10)
                }
                .buttonStyle(.bordered)
                .disabled(directorInput.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)

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
            .padding(.horizontal, 14)

            TextField("Комментарий к загружаемому документу", text: $directorNote)
                .textInputAutocapitalization(.never)
                .padding(10)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                .padding(.horizontal, 14)
                .padding(.bottom, 10)
                .focused($isDirectorNoteFocused)
        }
        .background(.ultraThinMaterial)
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

    private func statCapsule(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.subheadline.weight(.semibold))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
    }

    private func quickPromptButton(_ title: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.caption.weight(.semibold))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    Capsule()
                        .fill(Color.accentColor.opacity(0.12))
                )
        }
        .buttonStyle(.plain)
    }

    private func roleLoadCapsule(title: String, value: String, tint: Color, executor: String) -> some View {
        Button {
            selectedExecutorHistory = ExecutorHistoryTarget(id: executor, name: executor)
        } label: {
            VStack(alignment: .leading, spacing: 2) {
                Text(title)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Text(value)
                    .font(.subheadline.weight(.bold))
                    .foregroundStyle(tint)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(tint.opacity(0.10))
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private var taskRoleFilterStrip: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(TaskRoleFilter.allCases) { filter in
                    Button {
                        withAnimation(.easeInOut(duration: 0.18)) {
                            selectedTaskRoleFilter = filter
                        }
                    } label: {
                        Text(filter.rawValue)
                            .font(.caption.weight(.semibold))
                            .padding(.horizontal, 12)
                            .padding(.vertical, 8)
                            .background(
                                Capsule()
                                    .fill(selectedTaskRoleFilter == filter ? Color.accentColor.opacity(0.18) : Color(.secondarySystemBackground).opacity(useDarkMode ? 0.45 : 0.95))
                            )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
    }

    private func taskPlaceholder(_ text: String) -> some View {
        Text(text)
            .font(.footnote)
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func directorTaskRow(task: DirectorTask, completed: Bool) -> some View {
        let overdue = isTaskOverdue(task)
        return Button {
            selectedTaskID = task.id
        } label: {
            HStack(alignment: .top, spacing: 10) {
                Circle()
                    .fill(completed ? Color.green.opacity(0.18) : (overdue ? Color.red.opacity(0.18) : task.priority.color.opacity(0.18)))
                    .frame(width: 30, height: 30)
                    .overlay(
                        Image(systemName: completed ? "checkmark" : (overdue ? "exclamationmark" : "clock"))
                            .font(.caption.weight(.bold))
                            .foregroundStyle(completed ? Color.green : (overdue ? Color.red : task.priority.color))
                    )

                VStack(alignment: .leading, spacing: 4) {
                    Text(task.title)
                        .font(.footnote.weight(.semibold))
                        .multilineTextAlignment(.leading)
                    if !task.detail.isEmpty {
                        Text(task.detail)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(3)
                            .multilineTextAlignment(.leading)
                    }
                    HStack(spacing: 8) {
                        taskMetaChip(text: task.priority.rawValue, tint: task.priority.color)
                        if !completed {
                            taskMetaChip(text: task.stage.rawValue, tint: task.stage.color)
                        }
                        taskMetaChip(text: task.assignee, tint: .teal)
                        if let dueAt = task.dueAt, !dueAt.isEmpty, !completed {
                            taskMetaChip(text: overdue ? "Просрочено" : "Срок: \(dueAt)", tint: overdue ? .red : .blue)
                        }
                    }
                    Text(completed ? "Закрыто: \(task.completedAt ?? "—")" : "Создано: \(task.createdAt)")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                if completed {
                    Button {
                        reopenTask(task.id)
                    } label: {
                        Image(systemName: "arrow.uturn.backward.circle")
                            .font(.title3)
                    }
                    .buttonStyle(.plain)
                } else {
                    VStack(spacing: 10) {
                        Button {
                            advanceTaskStage(task.id)
                        } label: {
                            Image(systemName: stageIcon(task.stage))
                                .font(.title3)
                        }
                        .buttonStyle(.plain)

                        Button {
                            completeTask(task.id)
                        } label: {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.title3)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding(10)
            .background((overdue ? Color.red.opacity(0.08) : Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8)))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private func taskMetaChip(text: String, tint: Color) -> some View {
        return Text(text)
            .font(.caption2.weight(.semibold))
            .padding(.horizontal, 8)
            .padding(.vertical, 4)
            .background(tint.opacity(0.12))
            .foregroundStyle(tint)
            .clipShape(Capsule())
    }

    private func executionHighlightCard(_ snapshot: ExecutionSnapshot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .top) {
                Circle()
                    .fill(snapshot.needsRevision ? Color.orange.opacity(0.18) : Color.green.opacity(0.18))
                    .frame(width: 34, height: 34)
                    .overlay(
                        Image(systemName: snapshot.needsRevision ? "arrow.uturn.backward.circle.fill" : "checkmark.seal.fill")
                            .foregroundStyle(snapshot.needsRevision ? .orange : .green)
                    )
                VStack(alignment: .leading, spacing: 4) {
                    Text(snapshot.executor)
                        .font(.subheadline.weight(.semibold))
                    Text(snapshot.resultSummary)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }
                Spacer()
            }

            HStack(spacing: 8) {
                taskMetaChip(text: snapshot.status, tint: snapshot.needsRevision ? .orange : .green)
                taskMetaChip(text: snapshot.workerRole, tint: .blue)
            }

            if !snapshot.nextStep.isEmpty {
                Text("Следующий шаг: \(snapshot.nextStep)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            if !snapshot.resolution.isEmpty {
                Text("Резолюция: \(snapshot.resolution)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(10)
        .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func revisionFeedbackCard(_ snapshot: ExecutionSnapshot) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: "exclamationmark.bubble.fill")
                    .foregroundStyle(.orange)
                Text("Замечания директора")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(.orange)
            }
            Text(snapshot.revisionComments)
                .font(.caption)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(10)
        .background(Color.orange.opacity(0.10))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func executionInboxRow(_ snapshot: ExecutionSnapshot) -> some View {
        Button {
            isDirectorWorkspacePresented = true
        } label: {
            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 3) {
                        Text(snapshot.executor)
                            .font(.footnote.weight(.semibold))
                        Text(snapshot.resultSummary)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                    Spacer()
                    Text(snapshot.createdAt?.replacingOccurrences(of: "T", with: " ") ?? "сейчас")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }

                HStack(spacing: 8) {
                    taskMetaChip(text: snapshot.status, tint: snapshot.needsRevision ? .orange : .green)
                    taskMetaChip(text: snapshot.workerRole, tint: .teal)
                }

                if !snapshot.nextStep.isEmpty {
                    Text(snapshot.nextStep)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(10)
            .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
        .buttonStyle(.plain)
    }

    private func detailRow(title: String, value: String, tint: Color) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(.secondary)
                .frame(width: 92, alignment: .leading)
            Text(value)
                .font(.footnote.weight(.semibold))
                .foregroundStyle(tint)
                .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private func taskTimelineRow(_ event: DirectorTask.Event) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Circle()
                .fill(colorForTimelineTint(event.tint).opacity(0.18))
                .frame(width: 28, height: 28)
                .overlay(Image(systemName: timelineIcon(for: event.tint)).foregroundStyle(colorForTimelineTint(event.tint)))
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(event.title)
                        .font(.footnote.weight(.semibold))
                    Spacer()
                    Text(event.createdAt)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                if !event.detail.isEmpty {
                    Text(event.detail)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
        }
        .padding(10)
        .background(Color(.secondarySystemBackground).opacity(useDarkMode ? 0.35 : 0.8))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
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
                .fill(isAssistant ? Color(.secondarySystemBackground) : Color.white)
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

    @MainActor
    private func loadDirectorHistory() async {
        do {
            let response = try await api.directorHistory()
            directorMessages = response.messages
        } catch {
            statusText = "Ошибка загрузки диалога директора: \(error.localizedDescription)"
        }
    }

    @MainActor
    private func sendDirectorMessage() async {
        let text = directorInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        createTaskFromMessage(text)

        let localUserMessage = DirectorMessage(
            id: "local-\(UUID().uuidString)",
            role: "user",
            content: text,
            created_at: nowText()
        )
        directorMessages.append(localUserMessage)
        directorInput = ""
        isDirectorInputFocused = false

        isDirectorBusy = true
        statusText = "Директор анализирует задачу..."
        do {
            let response = try await api.directorSend(text: text)
            applyDirectorResponse(response)
            statusText = "Ответ директора получен"
        } catch {
            statusText = "Пробую восстановить связь с директором..."
            await autoRecover()
            do {
                let retry = try await api.directorSend(text: text)
                applyDirectorResponse(retry)
                statusText = "Ответ директора получен"
            } catch {
                statusText = "Директор временно недоступен: \(error.localizedDescription)"
            }
        }
        isDirectorBusy = false
    }

    @MainActor
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
            createTaskForDocument(name: name, note: directorNote)
            let response = try await api.directorUpload(
                filename: name,
                mimeType: mime,
                fileData: data,
                note: directorNote
            )
            applyDirectorResponse(response)
            lastUploadedFileName = name
            directorNote = ""
            isDirectorNoteFocused = false
            statusText = "Документ передан директору"
        } catch {
            statusText = "Ошибка загрузки документа: \(error.localizedDescription)"
        }
        isDirectorBusy = false
    }

    @MainActor
    private func applyDirectorResponse(_ response: DirectorChatResponse) {
        if let messages = response.messages {
            directorMessages = messages
        } else if let reply = response.reply, !reply.isEmpty {
            directorMessages.append(
                DirectorMessage(
                    id: "local-\(UUID().uuidString)",
                    role: "assistant",
                    content: reply,
                    created_at: nowText()
                )
            )
        }
        syncLatestTask(with: response.execution, reply: response.reply)
    }

    private var assistantMessages: [DirectorMessage] {
        directorMessages.filter { $0.role == "assistant" }
    }

    private var executionSnapshots: [ExecutionSnapshot] {
        assistantMessages.reversed().compactMap { message in
            executionSnapshot(from: message)
        }
    }

    private var activeDirectorTasks: [DirectorTask] {
        directorTasks
            .filter { !$0.isCompleted }
            .sorted(by: taskPriorityOrder)
    }

    private var completedDirectorTasks: [DirectorTask] {
        directorTasks
            .filter { $0.isCompleted }
            .sorted { ($0.completedAt ?? "") > ($1.completedAt ?? "") }
    }

    private var alertTasks: [DirectorTask] {
        activeDirectorTasks.filter { $0.unreadAlerts > 0 }
    }

    private var unreadAlertTasksCount: Int {
        alertTasks.reduce(0) { $0 + $1.unreadAlerts }
    }

    private var filteredActiveDirectorTasks: [DirectorTask] {
        activeDirectorTasks.filter(matchesSelectedRoleFilter)
    }

    private var filteredCompletedDirectorTasks: [DirectorTask] {
        completedDirectorTasks.filter(matchesSelectedRoleFilter)
    }

    private var documentTasks: [DirectorTask] {
        directorTasks
            .filter { $0.title.hasPrefix("Проверить документ:") }
            .sorted(by: taskPriorityOrder)
    }

    private var topExecutors: [String] {
        var ordered: [String] = []
        for task in directorTasks.sorted(by: taskPriorityOrder) {
            guard !task.assignee.isEmpty, !ordered.contains(task.assignee) else { continue }
            ordered.append(task.assignee)
        }
        return Array(ordered.prefix(4))
    }

    private var selectedTaskBinding: Binding<DirectorTask?> {
        Binding(
            get: {
                guard let selectedTaskID else { return nil }
                return directorTasks.first(where: { $0.id == selectedTaskID })
            },
            set: { newValue in
                selectedTaskID = newValue?.id
            }
        )
    }

    private func addManualTaskFromInput() {
        let text = directorInput.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        createTaskFromMessage(text)
        isDirectorInputFocused = false
        statusText = "Задача добавлена в контроль директора"
    }

    private func createTaskFromMessage(_ text: String) {
        let trimmed = text.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        let title = String((trimmed.components(separatedBy: .newlines).first ?? trimmed).prefix(80))
        let priority = detectPriority(from: trimmed)
        let task = DirectorTask(
            id: UUID().uuidString,
            title: title,
            detail: trimmed,
            createdAt: nowText(),
            dueAt: dueDateText(for: priority),
            priority: priority,
            assignee: inferAssignee(from: trimmed),
            stage: .new,
            completedAt: nil,
            timeline: [
                DirectorTask.Event(
                    id: UUID().uuidString,
                    title: "Задача создана",
                    detail: trimmed,
                    createdAt: nowText(),
                    tint: "blue"
                )
            ],
            unreadAlerts: 0
        )
        directorTasks.append(task)
        saveDirectorTasks()
    }

    private func createTaskForDocument(name: String, note: String) {
        let detail = note.trimmingCharacters(in: .whitespacesAndNewlines)
        let priority = detail.isEmpty ? DirectorTask.Priority.medium : detectPriority(from: detail)
        let task = DirectorTask(
            id: UUID().uuidString,
            title: "Проверить документ: \(name)",
            detail: detail,
            createdAt: nowText(),
            dueAt: dueDateText(for: priority),
            priority: priority,
            assignee: inferAssignee(from: detail.isEmpty ? name : detail),
            stage: .new,
            completedAt: nil,
            timeline: [
                DirectorTask.Event(
                    id: UUID().uuidString,
                    title: "Документ поставлен в работу",
                    detail: detail.isEmpty ? name : "\(name): \(detail)",
                    createdAt: nowText(),
                    tint: "blue"
                )
            ],
            unreadAlerts: 0
        )
        directorTasks.append(task)
        saveDirectorTasks()
    }

    private func completeTask(_ id: String) {
        guard let index = directorTasks.firstIndex(where: { $0.id == id }) else { return }
        directorTasks[index].stage = .control
        directorTasks[index].completedAt = nowText()
        appendTimelineEvent(
            to: id,
            title: "Задача завершена вручную",
            detail: "Пользователь отметил задачу исполненной.",
            tint: "green"
        )
        saveDirectorTasks()
        statusText = "Задача перенесена в исполненные"
    }

    private func reopenTask(_ id: String) {
        guard let index = directorTasks.firstIndex(where: { $0.id == id }) else { return }
        directorTasks[index].stage = .inProgress
        directorTasks[index].completedAt = nil
        appendTimelineEvent(
            to: id,
            title: "Задача возвращена в работу",
            detail: "Исполнение возобновлено после ручного возврата.",
            tint: "orange"
        )
        saveDirectorTasks()
        statusText = "Задача возвращена в текущие"
    }

    private func advanceTaskStage(_ id: String) {
        guard let index = directorTasks.firstIndex(where: { $0.id == id }) else { return }
        switch directorTasks[index].stage {
        case .new:
            directorTasks[index].stage = .inProgress
            appendTimelineEvent(to: id, title: "Задача переведена в работу", detail: "Поручение взято в исполнение.", tint: "orange")
            statusText = "Задача переведена в работу"
        case .inProgress:
            directorTasks[index].stage = .control
            appendTimelineEvent(to: id, title: "Задача переведена на контроль", detail: "Ожидается итоговый результат или проверка.", tint: "purple")
            statusText = "Задача переведена на контроль"
        case .control:
            directorTasks[index].stage = .new
            appendTimelineEvent(to: id, title: "Задача возвращена к исполнению", detail: "Контроль снят, задача снова активна.", tint: "blue")
            statusText = "Задача возвращена к исполнению"
        }
        saveDirectorTasks()
    }

    private func loadDirectorTasks() {
        guard let data = directorTasksJSON.data(using: .utf8),
              let decoded = try? JSONDecoder().decode([DirectorTask].self, from: data) else {
            directorTasks = []
            return
        }
        directorTasks = decoded
    }

    private func saveDirectorTasks() {
        guard let data = try? JSONEncoder().encode(directorTasks),
              let raw = String(data: data, encoding: .utf8) else {
            return
        }
        directorTasksJSON = raw
    }

    private var overdueDirectorTasks: [DirectorTask] {
        activeDirectorTasks.filter { isTaskOverdue($0) }
    }

    private var tasksInProgress: [DirectorTask] {
        activeDirectorTasks.filter { $0.stage == .inProgress }
    }

    private func isTaskOverdue(_ task: DirectorTask) -> Bool {
        guard !task.isCompleted,
              let dueAt = task.dueAt,
              let dueDate = taskDateFormatter.date(from: dueAt) else {
            return false
        }
        return Date() > dueDate
    }

    private func detectPriority(from text: String) -> DirectorTask.Priority {
        let normalized = text.lowercased()
        if normalized.contains("срочно") || normalized.contains("сегодня") || normalized.contains("крит") || normalized.contains("немедленно") {
            return .high
        }
        if normalized.contains("позже") || normalized.contains("на неделе") || normalized.contains("не срочно") {
            return .low
        }
        return .medium
    }

    private func inferAssignee(from text: String) -> String {
        let normalized = text.lowercased()
        if normalized.contains("договор") || normalized.contains("иск") || normalized.contains("юрист") || normalized.contains("суд") {
            return "Юрист"
        }
        if normalized.contains("смет") || normalized.contains("объект") || normalized.contains("пто") || normalized.contains("чертеж") {
            return "ПТО"
        }
        if normalized.contains("счет") || normalized.contains("оплат") || normalized.contains("фин") || normalized.contains("акт") {
            return "Финансы"
        }
        if normalized.contains("закуп") || normalized.contains("материал") || normalized.contains("поставка") {
            return "Снабжение"
        }
        return "Директор"
    }

    private func taskCount(for assignee: String) -> Int {
        activeDirectorTasks.filter { $0.assignee == assignee }.count
    }

    private func executorTasks(_ executor: String) -> [DirectorTask] {
        directorTasks.filter { $0.assignee == executor }.sorted(by: taskPriorityOrder)
    }

    private func executorHistorySubtitle(_ executor: String) -> String {
        let tasks = executorTasks(executor)
        if tasks.isEmpty {
            return "Задач пока нет."
        }
        let completed = tasks.filter(\.isCompleted).count
        let revisions = tasks.filter { latestRevisionText(for: $0) != nil }.count
        return "Всего задач: \(tasks.count), исполнено: \(completed), доработок: \(revisions)"
    }

    private func executorTint(_ executor: String) -> Color {
        switch executor {
        case "Юрист":
            return .indigo
        case "ПТО":
            return .teal
        case "Финансы":
            return .orange
        case "Снабжение":
            return .mint
        default:
            return .blue
        }
    }

    private func documentStatusText(for task: DirectorTask) -> String {
        if task.unreadAlerts > 0 {
            return "Есть новые замечания директора. Требуется доработка."
        }
        if task.isCompleted {
            return "Документ согласован и закрыт."
        }
        if let last = task.timeline.last {
            return last.detail.isEmpty ? last.title : last.detail
        }
        return task.detail.isEmpty ? "Документ ожидает обработки." : task.detail
    }

    private func taskPriorityOrder(_ lhs: DirectorTask, _ rhs: DirectorTask) -> Bool {
        let lhsScore = taskSortScore(lhs)
        let rhsScore = taskSortScore(rhs)
        if lhsScore != rhsScore {
            return lhsScore > rhsScore
        }
        return lhs.createdAt > rhs.createdAt
    }

    private func taskSortScore(_ task: DirectorTask) -> Int {
        var score = 0
        score += task.unreadAlerts * 100
        if isTaskOverdue(task) { score += 80 }
        switch task.priority {
        case .high:
            score += 40
        case .medium:
            score += 20
        case .low:
            score += 10
        }
        switch task.stage {
        case .inProgress:
            score += 15
        case .new:
            score += 10
        case .control:
            score += 5
        }
        return score
    }

    private func executionSnapshot(from message: DirectorMessage) -> ExecutionSnapshot? {
        let text = message.content
        let executor = firstMatch(in: text, pattern: #"(?m)^- Исполнитель:\s*(.+)$"#)
            ?? firstMatch(in: text, pattern: #"Результат возвращен на доработку исполнителю:\s*(.+)"#)
        let workerRole = firstMatch(in: text, pattern: #"(?m)^Роль:\s*(.+)$"#) ?? ""
        let resultSummary = firstMatch(in: text, pattern: #"(?m)^Результат:\s*(.+)$"#) ?? ""
        let status = firstMatch(in: text, pattern: #"(?m)^- Статус:\s*(.+)$"#)
            ?? (text.contains("возвращен на доработку") ? "возвращено на доработку" : "")
        let nextStep = firstMatch(in: text, pattern: #"(?m)^- Следующий шаг:\s*(.+)$"#) ?? ""
        let resolution = firstMatch(in: text, pattern: #"(?m)^- Резолюция:\s*(.+)$"#) ?? ""
        let needsRevision = text.contains("возвращен на доработку")
        let revisionComments = extractRevisionComments(from: text) ?? ""

        guard let executor, !executor.isEmpty else {
            return nil
        }

        return ExecutionSnapshot(
            id: message.id,
            executor: executor,
            workerRole: workerRole.isEmpty ? inferAssignee(from: text) : workerRole,
            status: status.isEmpty ? (needsRevision ? "возвращено на доработку" : "проверено") : status,
            resultSummary: resultSummary.isEmpty ? "Исполнитель отработал задачу и вернул результат директору." : resultSummary,
            nextStep: nextStep,
            resolution: resolution,
            needsRevision: needsRevision,
            createdAt: message.created_at,
            revisionComments: revisionComments
        )
    }

    private func syncLatestTask(with execution: DirectorExecution?, reply: String?) {
        guard let index = directorTasks.lastIndex(where: { !$0.isCompleted }) else { return }

        let parsedExecutor = execution?.executor?.trimmingCharacters(in: .whitespacesAndNewlines)
        let parsedStatus = execution?.status?.trimmingCharacters(in: .whitespacesAndNewlines).lowercased() ?? ""
        let parsedSummary = execution?.result_summary?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let parsedNextStep = execution?.next_step?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        let needsRevision = execution?.needs_revision == true || parsedStatus.contains("доработ")

        if let parsedExecutor, !parsedExecutor.isEmpty {
            directorTasks[index].assignee = parsedExecutor
        }

        if needsRevision {
            directorTasks[index].stage = .inProgress
            directorTasks[index].completedAt = nil
            directorTasks[index].unreadAlerts += 1
        } else if !parsedStatus.isEmpty {
            directorTasks[index].stage = .control
            directorTasks[index].completedAt = nowText()
            directorTasks[index].unreadAlerts = 0
        }

        var notes: [String] = []
        if !parsedSummary.isEmpty {
            notes.append("Результат: \(parsedSummary)")
        }
        if !parsedNextStep.isEmpty {
            notes.append("Следующий шаг: \(parsedNextStep)")
        }
        if let reply, needsRevision, let commentBlock = extractRevisionComments(from: reply), !commentBlock.isEmpty {
            notes.append(commentBlock)
        }

        if !notes.isEmpty {
            let joined = notes.joined(separator: "\n")
            if !directorTasks[index].detail.contains(joined) {
                directorTasks[index].detail = directorTasks[index].detail.isEmpty
                    ? joined
                    : "\(directorTasks[index].detail)\n\n\(joined)"
            }
        }

        if needsRevision {
            appendTimelineEvent(
                to: directorTasks[index].id,
                title: "Возврат на доработку",
                detail: extractRevisionComments(from: reply ?? "") ?? "Директор вернул результат с замечаниями.",
                tint: "orange"
            )
        } else if !parsedStatus.isEmpty {
            appendTimelineEvent(
                to: directorTasks[index].id,
                title: "Результат принят директором",
                detail: parsedSummary.isEmpty ? "Исполнитель завершил работу, директор подтвердил результат." : parsedSummary,
                tint: "green"
            )
        }

        saveDirectorTasks()
    }

    private func appendTimelineEvent(to id: String, title: String, detail: String, tint: String) {
        guard let index = directorTasks.firstIndex(where: { $0.id == id }) else { return }
        if let last = directorTasks[index].timeline.last,
           last.title == title,
           last.detail == detail,
           last.tint == tint {
            return
        }
        let event = DirectorTask.Event(
            id: UUID().uuidString,
            title: title,
            detail: detail,
            createdAt: nowText(),
            tint: tint
        )
        directorTasks[index].timeline.append(event)
    }

    private func latestRevisionText(for task: DirectorTask) -> String? {
        task.timeline.last(where: { $0.tint == "orange" })?.detail
    }

    private func markTaskAlertsRead(_ id: String) {
        guard let index = directorTasks.firstIndex(where: { $0.id == id }) else { return }
        directorTasks[index].unreadAlerts = 0
        saveDirectorTasks()
    }

    private func colorForTimelineTint(_ tint: String) -> Color {
        switch tint {
        case "green":
            return .green
        case "orange":
            return .orange
        case "purple":
            return .purple
        case "red":
            return .red
        default:
            return .blue
        }
    }

    private func timelineIcon(for tint: String) -> String {
        switch tint {
        case "green":
            return "checkmark.circle.fill"
        case "orange":
            return "arrow.uturn.backward.circle.fill"
        case "purple":
            return "eye.circle.fill"
        case "red":
            return "exclamationmark.triangle.fill"
        default:
            return "circle.fill"
        }
    }

    private func extractRevisionComments(from text: String) -> String? {
        guard let range = text.range(of: "Замечания директора:") else { return nil }
        let block = String(text[range.lowerBound...])
            .components(separatedBy: "\n")
            .prefix(4)
            .joined(separator: "\n")
        return block.isEmpty ? nil : block
    }

    private func matchesSelectedRoleFilter(_ task: DirectorTask) -> Bool {
        switch selectedTaskRoleFilter {
        case .all:
            return true
        case .director:
            return task.assignee == "Директор"
        case .legal:
            return task.assignee == "Юрист"
        case .pto:
            return task.assignee == "ПТО"
        case .finance:
            return task.assignee == "Финансы"
        case .supply:
            return task.assignee == "Снабжение"
        }
    }

    private func firstMatch(in text: String, pattern: String) -> String? {
        guard let regex = try? NSRegularExpression(pattern: pattern) else { return nil }
        let range = NSRange(text.startIndex..., in: text)
        guard let match = regex.firstMatch(in: text, range: range),
              match.numberOfRanges > 1,
              let captureRange = Range(match.range(at: 1), in: text) else {
            return nil
        }
        return String(text[captureRange]).trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private func dueDateText(for priority: DirectorTask.Priority) -> String {
        let calendar = Calendar.current
        let now = Date()
        let dueDate: Date
        switch priority {
        case .high:
            dueDate = calendar.date(byAdding: .hour, value: 8, to: now) ?? now
        case .medium:
            dueDate = calendar.date(byAdding: .day, value: 2, to: now) ?? now
        case .low:
            dueDate = calendar.date(byAdding: .day, value: 5, to: now) ?? now
        }
        return taskDateFormatter.string(from: dueDate)
    }

    private func stageIcon(_ stage: DirectorTask.Stage) -> String {
        switch stage {
        case .new: return "play.circle"
        case .inProgress: return "arrow.triangle.2.circlepath.circle"
        case .control: return "eye.circle"
        }
    }

    private var taskDateFormatter: DateFormatter {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ru_RU")
        formatter.dateFormat = "dd.MM.yyyy HH:mm"
        return formatter
    }

    private func mimeType(for url: URL) -> String {
        if let type = UTType(filenameExtension: url.pathExtension),
           let mime = type.preferredMIMEType {
            return mime
        }
        return "application/octet-stream"
    }
}
