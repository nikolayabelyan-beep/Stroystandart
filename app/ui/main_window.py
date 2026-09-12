"""
Главное окно приложения.
Навигация по разделам и управление объектами.
"""
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QListWidget, QListWidgetItem, QStackedWidget,
    QLabel, QPushButton, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QMenu, QMenuBar
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon, QAction

from app.database.repositories import ProjectRepository
from app.database.models.models import Project
from app.ui.project_widget import ProjectWidget
from app.ui.projects_list_widget import ProjectsListWidget
from app.ui.vor_widget import VorWidget
from app.ui.settings_widget import SettingsWidget


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("СтройДокумент - Ведение исполнительной документации")
        self.setMinimumSize(1400, 900)
        
        # Текущий проект
        self.current_project: Project = None
        
        # Инициализация UI
        self._init_ui()
        self._init_menu_bar()
        self._init_toolbar()
        self._init_status_bar()
        
        # Загрузка списка проектов
        self._load_projects()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter для разделения панели проектов и рабочей области
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - список проектов
        left_panel = QWidget()
        left_panel.setMaximumWidth(350)
        left_panel.setMinimumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Заголовок
        projects_label = QLabel("📁 Объекты")
        projects_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #f0f0f0;
                border-radius: 5px;
            }
        """)
        left_layout.addWidget(projects_label)
        
        # Список проектов
        self.projects_list = ProjectsListWidget()
        self.projects_list.itemClicked.connect(self._on_project_selected)
        left_layout.addWidget(self.projects_list)
        
        # Кнопка добавления проекта
        add_project_btn = QPushButton("+ Добавить объект")
        add_project_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_project_btn.clicked.connect(self._add_project)
        left_layout.addWidget(add_project_btn)
        
        splitter.addWidget(left_panel)
        
        # Правая панель - рабочая область
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Stacked widget для переключения между видами
        self.stack = QStackedWidget()
        
        # Виджет приветствия (когда проект не выбран)
        welcome_widget = self._create_welcome_widget()
        self.stack.addWidget(welcome_widget)
        
        # Виджет проекта
        self.project_widget = ProjectWidget()
        self.stack.addWidget(self.project_widget)
        
        # Виджет настроек
        self.settings_widget = SettingsWidget()
        self.stack.addWidget(self.settings_widget)
        
        right_layout.addWidget(self.stack)
        splitter.addWidget(right_panel)
        
        # Настройка splitter
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 1100])
        
        main_layout.addWidget(splitter)
    
    def _create_welcome_widget(self) -> QWidget:
        """Создать виджет приветствия."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        
        label = QLabel("""
        <h1>Добро пожаловать в СтройДокумент</h1>
        <p style='font-size: 18px; color: #666;'>
            Система ведения исполнительной документации<br>
            для объектов капитального строительства
        </p>
        <p style='font-size: 14px; color: #999; margin-top: 30px;'>
            Выберите объект слева или создайте новый
        </p>
        """)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        return widget
    
    def _init_menu_bar(self):
        """Инициализация меню."""
        menubar = self.menuBar()
        
        # Файл
        file_menu = menubar.addMenu("Файл")
        
        export_action = QAction("Экспорт базы данных", self)
        export_action.triggered.connect(self._export_database)
        file_menu.addAction(export_action)
        
        import_action = QAction("Импорт базы данных", self)
        import_action.triggered.connect(self._import_database)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_toolbar(self):
        """Инициализация панели инструментов."""
        toolbar = QToolBar("Основная панель")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Кнопка настроек
        settings_action = toolbar.addAction("⚙️ Настройки")
        settings_action.triggered.connect(self._show_settings)
        
        toolbar.addSeparator()
        
        # Кнопка обновления
        refresh_action = toolbar.addAction("🔄 Обновить")
        refresh_action.triggered.connect(self._load_projects)
    
    def _init_status_bar(self):
        """Инициализация строки состояния."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Готов к работе")
    
    def _load_projects(self):
        """Загрузить список проектов."""
        self.projects_list.load_projects()
    
    @Slot()
    def _add_project(self):
        """Добавить новый проект."""
        from app.ui.project_dialog import ProjectDialog
        
        dialog = ProjectDialog(self)
        if dialog.exec():
            project_data = dialog.get_project_data()
            if project_data:
                project = Project(**project_data)
                project_id = ProjectRepository.create(project)
                
                if project_id > 0:
                    self.statusbar.showMessage(f"Объект '{project.name}' создан")
                    self._load_projects()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось создать объект")
    
    @Slot(QListWidgetItem)
    def _on_project_selected(self, item: QListWidgetItem):
        """Обработчик выбора проекта."""
        project_id = item.data(Qt.UserRole)
        
        if project_id:
            project = ProjectRepository.get_by_id(project_id)
            if project:
                self.current_project = project
                self.project_widget.load_project(project)
                self.stack.setCurrentIndex(1)
                self.statusbar.showMessage(f"Открыт объект: {project.name}")
    
    @Slot()
    def _show_settings(self):
        """Показать настройки."""
        self.stack.setCurrentIndex(2)
    
    @Slot()
    def _export_database(self):
        """Экспорт базы данных."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт базы данных",
            "",
            "SQLite Database (*.db)"
        )
        
        if file_path:
            from app.database.db_manager import DatabaseManager
            import shutil
            
            db = DatabaseManager.get_instance()
            try:
                shutil.copy(str(db.db_path), file_path)
                QMessageBox.information(
                    self,
                    "Успешно",
                    f"База данных экспортирована в:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать базу данных:\n{e}")
    
    @Slot()
    def _import_database(self):
        """Импорт базы данных."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт базы данных",
            "",
            "SQLite Database (*.db)"
        )
        
        if file_path:
            reply = QMessageBox.warning(
                self,
                "Предупреждение",
                "Импорт базы данных заменит текущие данные. Продолжить?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                from app.database.db_manager import DatabaseManager
                import shutil
                
                db = DatabaseManager.get_instance()
                try:
                    shutil.copy(file_path, str(db.db_path))
                    QMessageBox.information(
                        self,
                        "Успешно",
                        "База данных импортирована.\nПриложение будет перезапущено."
                    )
                    self._load_projects()
                except Exception as e:
                    QMessageBox.critical(self, "Ошибка", f"Не удалось импортировать базу данных:\n{e}")
    
    @Slot()
    def _show_about(self):
        """Показать информацию о программе."""
        QMessageBox.about(
            self,
            "О программе",
            """<h2>СтройДокумент v1.0.0</h2>
            <p>Система ведения исполнительной документации<br>
            для объектов капитального строительства.</p>
            <p><b>Основные возможности:</b></p>
            <ul>
                <li>Управление объектами строительства</li>
                <li>Ведение ВОР (ведомости объёмов работ)</li>
                <li>Генерация АОСР и исполнительных схем</li>
                <li>Локальный ИИ для анализа работ</li>
                <li>Формирование КС-2 и КС-3</li>
                <li>Контроль комплектности документации</li>
            </ul>
            <p>Все данные хранятся локально на вашем компьютере.</p>
            """
        )
