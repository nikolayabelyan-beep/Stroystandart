"""
Виджет проекта с навигацией по разделам.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt

from app.database.models.models import Project
from app.ui.vor_widget import VorWidget
from app.ui.documents_widget import DocumentsWidget
from app.ui.project_info_widget import ProjectInfoWidget


class ProjectWidget(QWidget):
    """Виджет проекта с вкладками разделов."""
    
    def __init__(self):
        super().__init__()
        
        self.current_project: Project = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Заголовок проекта
        header_widget = self._create_header()
        layout.addWidget(header_widget)
        
        # Вкладки разделов
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-top: none;
                background-color: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 2px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                background-color: #f5f5f5;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
                margin-bottom: -1px;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e8e8e8;
            }
        """)
        
        # Добавление вкладок
        self.info_widget = ProjectInfoWidget()
        self.tabs.addTab(self.info_widget, "📋 Общая информация")
        
        self.vor_widget = VorWidget()
        self.tabs.addTab(self.vor_widget, "📊 ВОР")
        
        self.documents_widget = DocumentsWidget()
        self.tabs.addTab(self.documents_widget, "📁 Исполнительная документация")
        
        # Пока заглушки для будущих разделов
        materials_widget = QLabel("📦 Материалы и сертификаты\n(Раздел в разработке)")
        materials_widget.setAlignment(Qt.AlignCenter)
        materials_widget.setStyleSheet("font-size: 16px; color: #999; padding: 50px;")
        self.tabs.addTab(materials_widget, "📦 Материалы")
        
        schemas_widget = QLabel("📐 Исполнительные схемы\n(Раздел в разработке)")
        schemas_widget.setAlignment(Qt.AlignCenter)
        schemas_widget.setStyleSheet("font-size: 16px; color: #999; padding: 50px;")
        self.tabs.addTab(schemas_widget, "📐 Схемы")
        
        photos_widget = QLabel("📷 Фотофиксация\n(Раздел в разработке)")
        photos_widget.setAlignment(Qt.AlignCenter)
        photos_widget.setStyleSheet("font-size: 16px; color: #999; padding: 50px;")
        self.tabs.addTab(photos_widget, "📷 Фото")
        
        ks_widget = QLabel("📄 КС-2, КС-3\n(Раздел в разработке)")
        ks_widget.setAlignment(Qt.AlignCenter)
        ks_widget.setStyleSheet("font-size: 16px; color: #999; padding: 50px;")
        self.tabs.addTab(ks_widget, "📄 КС-2/КС-3")
        
        ai_widget = QLabel("🤖 Локальный ИИ\n(Раздел в разработке)")
        ai_widget.setAlignment(Qt.AlignCenter)
        ai_widget.setStyleSheet("font-size: 16px; color: #999; padding: 50px;")
        self.tabs.addTab(ai_widget, "🤖 ИИ помощник")
        
        layout.addWidget(self.tabs)
    
    def _create_header(self) -> QWidget:
        """Создать заголовок проекта."""
        widget = QWidget()
        widget.setStyleSheet("""
            QWidget {
                background-color: #1976d2;
                color: white;
                padding: 15px;
            }
        """)
        
        layout = QHBoxLayout(widget)
        
        self.header_label = QLabel("Объект не выбран")
        self.header_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: white;
            }
        """)
        layout.addWidget(self.header_label)
        
        layout.addStretch()
        
        # Кнопки действий
        add_vor_btn = QPushButton("+ Добавить работу")
        add_vor_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_vor_btn.clicked.connect(self._add_work_item)
        layout.addWidget(add_vor_btn)
        
        return widget
    
    def load_project(self, project: Project):
        """Загрузить проект в виджет."""
        self.current_project = project
        
        # Обновление заголовка
        self.header_label.setText(f"🏗️ {project.name}")
        
        # Загрузка данных в виджеты
        self.info_widget.load_project(project)
        self.vor_widget.load_project(project)
        self.documents_widget.load_project(project)
        
        # Переключение на первую вкладку
        self.tabs.setCurrentIndex(0)
    
    def _add_work_item(self):
        """Добавить работу (передаём в ВОР)."""
        if self.current_project:
            self.tabs.setCurrentIndex(1)  # Переключение на вкладку ВОР
            self.vor_widget.show_add_dialog()
