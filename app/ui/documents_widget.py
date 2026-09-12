"""
Виджет списка документов проекта.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QMenu, QLabel
)
from PySide6.QtCore import Qt

from app.database.models.models import Project, Document
from app.database.repositories import DocumentRepository


class DocumentsWidget(QWidget):
    """Виджет исполнительной документации."""
    
    def __init__(self):
        super().__init__()
        
        self.current_project: Project = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Заголовок
        header_label = QLabel("📁 Реестр исполнительной документации")
        header_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #f5f5f5;
                border-radius: 5px;
            }
        """)
        layout.addWidget(header_label)
        
        # Таблица документов
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "№", "Тип документа", "Номер", "Дата", "Работа", "Статус"
        ])
        
        # Настройка таблицы
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #ddd;
                font-weight: bold;
            }
        """)
        
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.table)
        
        # Кнопки действий
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        add_doc_btn = QPushButton("+ Добавить документ")
        add_doc_btn.clicked.connect(self._add_document)
        add_doc_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(add_doc_btn)
        
        layout.addLayout(button_layout)
    
    def load_project(self, project: Project):
        """Загрузить проект и его документы."""
        self.current_project = project
        self._load_documents()
    
    def _load_documents(self):
        """Загрузить документы из базы данных."""
        if not self.current_project:
            return
        
        self.table.setRowCount(0)
        
        documents = DocumentRepository.get_by_project(self.current_project.id)
        
        status_map = {
            "draft": "📝 Черновик",
            "requires_review": "🔍 Требует проверки",
            "ready": "✅ Готово",
            "approved": "✓ Подписано",
            "submitted": "📤 Передано заказчику"
        }
        
        for i, doc in enumerate(documents):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Номер
            self.table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            
            # Тип
            type_item = QTableWidgetItem(doc.document_type)
            type_item.setData(Qt.UserRole, doc.id)
            self.table.setItem(row, 1, type_item)
            
            # Номер
            self.table.setItem(row, 2, QTableWidgetItem(doc.document_number or "-"))
            
            # Дата
            date_str = doc.document_date.strftime("%d.%m.%Y") if doc.document_date else "-"
            self.table.setItem(row, 3, QTableWidgetItem(date_str))
            
            # Работа
            work_name = self._get_work_name(doc.work_item_id)
            self.table.setItem(row, 4, QTableWidgetItem(work_name))
            
            # Статус
            status_text = status_map.get(doc.status, doc.status)
            self.table.setItem(row, 5, QTableWidgetItem(status_text))
    
    def _get_work_name(self, work_item_id: int) -> str:
        """Получить название работы по ID."""
        if not work_item_id:
            return "Общестроительные работы"
        
        from app.database.repositories import WorkItemRepository
        
        work_item = WorkItemRepository.get_by_id(work_item_id)
        return work_item.work_name if work_item else "Не найдено"
    
    def _show_context_menu(self, position):
        """Показать контекстное меню."""
        row = self.table.rowAt(position.y())
        
        if row < 0:
            return
        
        item = self.table.item(row, 1)
        if not item:
            return
        
        doc_id = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        open_action = menu.addAction("📂 Открыть")
        open_action.triggered.connect(lambda: self._open_document(doc_id))
        
        edit_action = menu.addAction("✏️ Редактировать")
        edit_action.triggered.connect(lambda: self._edit_document(doc_id))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Удалить")
        delete_action.triggered.connect(lambda: self._delete_document(doc_id))
        
        menu.exec_(self.table.viewport().mapToGlobal(position))
    
    def _open_document(self, doc_id: int):
        """Открыть документ."""
        QMessageBox.information(
            self,
            "Открытие документа",
            f"Документ ID: {doc_id}\n\n(Функция в разработке)"
        )
    
    def _edit_document(self, doc_id: int):
        """Редактировать документ."""
        QMessageBox.information(
            self,
            "Редактирование документа",
            f"Документ ID: {doc_id}\n\n(Функция в разработке)"
        )
    
    def _delete_document(self, doc_id: int):
        """Удалить документ."""
        reply = QMessageBox.warning(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот документ?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if DocumentRepository.delete(doc_id):
                self._load_documents()
                QMessageBox.information(self, "Успешно", "Документ удалён")
    
    def _add_document(self):
        """Добавить документ."""
        QMessageBox.information(
            self,
            "Добавление документа",
            "Форма добавления документа находится в разработке"
        )
