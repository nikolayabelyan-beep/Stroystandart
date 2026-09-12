"""
Виджет ВОР (ведомости объёмов работ).
Таблица с работами, импорт/экспорт, анализ ИИ.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QMenu, QDialog, QFormLayout, QLineEdit,
    QDoubleSpinBox, QComboBox, QTextEdit, QLabel, QAbstractItemView
)
from PySide6.QtCore import Qt, Slot

from app.database.models.models import Project, WorkItem
from app.database.repositories import WorkItemRepository


class VorWidget(QWidget):
    """Виджет ВОР."""
    
    def __init__(self):
        super().__init__()
        
        self.current_project: Project = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Панель инструментов
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Таблица ВОР
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "№", "Наименование работы", "Ед.", "План", "Факт", "Остаток",
            "Участок", "Тип", "Статус"
        ])
        
        # Настройка таблицы
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
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
    
    def _create_toolbar(self) -> QWidget:
        """Создать панель инструментов."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Кнопка добавления
        add_btn = QPushButton("+ Добавить работу")
        add_btn.clicked.connect(self.show_add_dialog)
        add_btn.setStyleSheet("""
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
        layout.addWidget(add_btn)
        
        # Кнопка импорта
        import_btn = QPushButton("📥 Импорт")
        import_btn.clicked.connect(self._import_vor)
        layout.addWidget(import_btn)
        
        # Кнопка экспорта
        export_btn = QPushButton("📤 Экспорт")
        export_btn.clicked.connect(self._export_vor)
        layout.addWidget(export_btn)
        
        layout.addStretch()
        
        # Кнопка анализа ИИ
        ai_btn = QPushButton("🤖 Анализ ИИ")
        ai_btn.clicked.connect(self._analyze_with_ai)
        ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        layout.addWidget(ai_btn)
        
        return widget
    
    def load_project(self, project: Project):
        """Загрузить проект и его ВОР."""
        self.current_project = project
        self._load_work_items()
    
    def _load_work_items(self):
        """Загрузить элементы ВОР из базы данных."""
        if not self.current_project:
            return
        
        self.table.setRowCount(0)
        
        work_items = WorkItemRepository.get_by_project(self.current_project.id)
        
        for i, item in enumerate(work_items):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Номер
            self.table.setItem(row, 0, QTableWidgetItem(str(i + 1)))
            
            # Наименование
            name_item = QTableWidgetItem(item.work_name)
            name_item.setData(Qt.UserRole, item.id)
            self.table.setItem(row, 1, name_item)
            
            # Единица
            self.table.setItem(row, 2, QTableWidgetItem(item.unit or "-"))
            
            # План
            plan_item = QTableWidgetItem(f"{item.planned_quantity:.2f}")
            plan_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 3, plan_item)
            
            # Факт
            fact_item = QTableWidgetItem(f"{item.actual_quantity:.2f}")
            fact_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 4, fact_item)
            
            # Остаток
            remaining = item.planned_quantity - item.actual_quantity
            remaining_item = QTableWidgetItem(f"{remaining:.2f}")
            remaining_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if remaining > 0:
                remaining_item.setForeground(Qt.darkYellow)
            elif remaining < 0:
                remaining_item.setForeground(Qt.red)
            else:
                remaining_item.setForeground(Qt.darkGreen)
            self.table.setItem(row, 5, remaining_item)
            
            # Участок
            location = item.location or item.floor or item.axis or "-"
            self.table.setItem(row, 6, QTableWidgetItem(location))
            
            # Тип
            work_type = item.work_type or "Общестроительные"
            self.table.setItem(row, 7, QTableWidgetItem(work_type))
            
            # Статус
            status_map = {
                "planned": "📋 Запланировано",
                "in_progress": "🔨 В работе",
                "completed": "✅ Выполнено",
                "verified": "✓ Проверено",
                "approved": "✓ Согласовано"
            }
            status_text = status_map.get(item.status, item.status)
            self.table.setItem(row, 8, QTableWidgetItem(status_text))
    
    @Slot()
    def show_add_dialog(self):
        """Показать диалог добавления работы."""
        if not self.current_project:
            QMessageBox.warning(self, "Ошибка", "Объект не выбран")
            return
        
        from app.ui.work_item_dialog import WorkItemDialog
        
        dialog = WorkItemDialog(self, self.current_project.id)
        if dialog.exec():
            work_data = dialog.get_work_data()
            if work_data:
                work_item = WorkItem(**work_data)
                work_id = WorkItemRepository.create(work_item)
                
                if work_id > 0:
                    QMessageBox.information(self, "Успешно", "Работа добавлена")
                    self._load_work_items()
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить работу")
    
    def _show_context_menu(self, position):
        """Показать контекстное меню."""
        row = self.table.rowAt(position.y())
        
        if row < 0:
            return
        
        item = self.table.item(row, 1)
        if not item:
            return
        
        work_id = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        edit_action = menu.addAction("✏️ Редактировать")
        edit_action.triggered.connect(lambda: self._edit_work_item(work_id))
        
        delete_action = menu.addAction("🗑️ Удалить")
        delete_action.triggered.connect(lambda: self._delete_work_item(work_id))
        
        menu.addSeparator()
        
        actual_action = menu.addAction("📊 Внести факт. объём")
        actual_action.triggered.connect(lambda: self._update_actual_quantity(work_id))
        
        menu.exec_(self.table.viewport().mapToGlobal(position))
    
    def _edit_work_item(self, work_id: int):
        """Редактировать работу."""
        work_item = WorkItemRepository.get_by_id(work_id)
        
        if not work_item:
            return
        
        from app.ui.work_item_dialog import WorkItemDialog
        
        dialog = WorkItemDialog(self, self.current_project.id, work_item)
        if dialog.exec():
            updated_data = dialog.get_work_data()
            if updated_data:
                updated_data['id'] = work_id
                updated_item = WorkItem(**updated_data)
                
                if WorkItemRepository.update(updated_item):
                    QMessageBox.information(self, "Успешно", "Работа обновлена")
                    self._load_work_items()
    
    def _delete_work_item(self, work_id: int):
        """Удалить работу."""
        reply = QMessageBox.warning(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить эту работу?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if WorkItemRepository.delete(work_id):
                self._load_work_items()
                QMessageBox.information(self, "Успешно", "Работа удалена")
    
    def _update_actual_quantity(self, work_id: int):
        """Обновить фактический объём."""
        work_item = WorkItemRepository.get_by_id(work_id)
        
        if not work_item:
            return
        
        from app.ui.actual_quantity_dialog import ActualQuantityDialog
        
        dialog = ActualQuantityDialog(self, work_item)
        if dialog.exec():
            quantity = dialog.get_quantity()
            if quantity is not None:
                work_item.actual_quantity = quantity
                work_item.update_quantities()
                
                # Проверка превышения
                if work_item.actual_quantity > work_item.planned_quantity:
                    QMessageBox.warning(
                        self,
                        "Предупреждение",
                        f"Фактический объём ({work_item.actual_quantity}) превышает плановый ({work_item.planned_quantity})!"
                    )
                
                if WorkItemRepository.update(work_item):
                    self._load_work_items()
                    QMessageBox.information(self, "Успешно", "Объём обновлён")
    
    def _import_vor(self):
        """Импорт ВОР из файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт ВОР",
            "",
            "Excel Files (*.xlsx *.xls);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            QMessageBox.information(
                self,
                "Импорт",
                f"Будет выполнен импорт из файла:\n{file_path}\n\n(Функция в разработке)"
            )
    
    def _export_vor(self):
        """Экспорт ВОР в файл."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт ВОР",
            "vor.xlsx",
            "Excel Files (*.xlsx)"
        )
        
        if file_path:
            QMessageBox.information(
                self,
                "Экспорт",
                f"Будет выполнен экспорт в файл:\n{file_path}\n\n(Функция в разработке)"
            )
    
    def _analyze_with_ai(self):
        """Анализ ВОР с помощью локального ИИ."""
        QMessageBox.information(
            self,
            "Анализ ИИ",
            "Функция анализа ВОР с помощью локального ИИ находится в разработке.\n\n"
            "Для работы требуется установленный Ollama или llama.cpp."
        )
