"""
Диалог добавления/редактирования работы ВОР.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit,
    QPushButton, QMessageBox, QGroupBox, QWidget, QScrollArea
)
from PySide6.QtCore import Qt

from app.database.models.models import WorkItem


class WorkItemDialog(QDialog):
    """Диалог добавления/редактирования работы."""
    
    def __init__(self, parent=None, project_id: int = None, work_item: WorkItem = None):
        super().__init__(parent)
        
        self.project_id = project_id
        self.work_item = work_item
        self.is_edit = work_item is not None
        
        if self.is_edit:
            self.setWindowTitle("Редактирование работы")
        else:
            self.setWindowTitle("Добавить работу")
        
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        
        self._init_ui()
        
        if self.is_edit:
            self._load_work_data()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # Основная информация
        main_group = QGroupBox("📋 Основная информация")
        main_form = QFormLayout()
        main_form.setSpacing(10)
        
        # Номер ВОР
        self.vor_number_edit = QLineEdit()
        self.vor_number_edit.setPlaceholderText("1.1")
        main_form.addRow("№ ВОР", self.vor_number_edit)
        
        # Наименование работы
        self.work_name_edit = QLineEdit()
        self.work_name_edit.setPlaceholderText("Устройство монолитных железобетонных стен")
        main_form.addRow("Наименование*", self.work_name_edit)
        
        # Единица измерения
        self.unit_combo = QComboBox()
        self.unit_combo.setEditable(True)
        units = ["м3", "м2", "м", "т", "кг", "шт", "компл", "п.м."]
        for unit in units:
            self.unit_combo.addItem(unit)
        main_form.addRow("Ед. изм.", self.unit_combo)
        
        # Плановый объём
        self.planned_spin = QDoubleSpinBox()
        self.planned_spin.setRange(0, 999999)
        self.planned_spin.setDecimals(2)
        self.planned_spin.setValue(0)
        main_form.addRow("Плановый объём*", self.planned_spin)
        
        main_group.setLayout(main_form)
        scroll_layout.addWidget(main_group)
        
        # Расположение
        location_group = QGroupBox("📍 Расположение")
        location_form = QFormLayout()
        location_form.setSpacing(10)
        
        # Участок
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Участок 1")
        location_form.addRow("Участок", self.location_edit)
        
        # Этаж
        self.floor_edit = QLineEdit()
        self.floor_edit.setPlaceholderText("1-3")
        location_form.addRow("Этаж", self.floor_edit)
        
        # Оси
        self.axis_edit = QLineEdit()
        self.axis_edit.setPlaceholderText("1-5/А-Г")
        location_form.addRow("Оси", self.axis_edit)
        
        # Отметка
        self.elevation_edit = QLineEdit()
        self.elevation_edit.setPlaceholderText("+3.150")
        location_form.addRow("Отметка", self.elevation_edit)
        
        location_group.setLayout(location_form)
        scroll_layout.addWidget(location_group)
        
        # Тип работы
        type_group = QGroupBox("🏷️ Тип работы")
        type_form = QFormLayout()
        
        # Тип работ
        self.work_type_combo = QComboBox()
        self.work_type_combo.setEditable(True)
        for work_type in WorkItem.WORK_TYPES:
            self.work_type_combo.addItem(work_type)
        type_form.addRow("Тип работ", self.work_type_combo)
        
        # Скрытая работа
        self.hidden_combo = QComboBox()
        self.hidden_combo.addItem("Нет", False)
        self.hidden_combo.addItem("Да", True)
        self.hidden_combo.addItem("Частично (смешанная)", None)
        type_form.addRow("Скрытая работа", self.hidden_combo)
        
        # Материал
        self.material_edit = QLineEdit()
        self.material_edit.setPlaceholderText("Бетон В25, арматура А500С")
        type_form.addRow("Материал", self.material_edit)
        
        type_group.setLayout(type_form)
        scroll_layout.addWidget(type_group)
        
        # Документы
        docs_group = QGroupBox("📄 Проектная документация")
        docs_form = QFormLayout()
        docs_form.setSpacing(10)
        
        # Чертежи
        self.drawing_edit = QLineEdit()
        self.drawing_edit.setPlaceholderText("АР-5, КЖ-12")
        docs_form.addRow("Номер чертежа", self.drawing_edit)
        
        # Проектный документ
        self.project_doc_edit = QLineEdit()
        self.project_doc_edit.setPlaceholderText("Раздел 5. ПЗ")
        docs_form.addRow("Проектный документ", self.project_doc_edit)
        
        # Нормативные документы
        self.normative_edit = QTextEdit()
        self.normative_edit.setMaximumHeight(80)
        self.normative_edit.setPlaceholderText("СП 63.13330.2018, ГОСТ Р 54257-2011")
        docs_form.addRow("Нормативные документы", self.normative_edit)
        
        docs_group.setLayout(docs_form)
        scroll_layout.addWidget(docs_group)
        
        # Примечания
        notes_group = QGroupBox("📝 Примечания")
        notes_form = QFormLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Дополнительная информация...")
        notes_form.addRow("Примечания", self.notes_edit)
        
        notes_group.setLayout(notes_form)
        scroll_layout.addWidget(notes_group)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_work_data(self):
        """Загрузить данные работы в форму."""
        if not self.work_item:
            return
        
        self.vor_number_edit.setText(self.work_item.vor_number or "")
        self.work_name_edit.setText(self.work_item.work_name)
        
        # Установка единицы
        index = self.unit_combo.findText(self.work_item.unit)
        if index >= 0:
            self.unit_combo.setCurrentIndex(index)
        else:
            self.unit_combo.setCurrentText(self.work_item.unit or "")
        
        self.planned_spin.setValue(self.work_item.planned_quantity)
        self.location_edit.setText(self.work_item.location or "")
        self.floor_edit.setText(self.work_item.floor or "")
        self.axis_edit.setText(self.work_item.axis or "")
        self.elevation_edit.setText(self.work_item.elevation or "")
        
        # Тип работ
        index = self.work_type_combo.findText(self.work_item.work_type)
        if index >= 0:
            self.work_type_combo.setCurrentIndex(index)
        else:
            self.work_type_combo.setCurrentText(self.work_item.work_type or "")
        
        # Скрытая работа
        if self.work_item.hidden_work:
            self.hidden_combo.setCurrentIndex(1)
        else:
            self.hidden_combo.setCurrentIndex(0)
        
        self.material_edit.setText(self.work_item.material or "")
        self.drawing_edit.setText(self.work_item.drawing_number or "")
        self.project_doc_edit.setText(self.work_item.project_document or "")
        self.normative_edit.setText(self.work_item.normative_documents or "")
        self.notes_edit.setText(self.work_item.notes or "")
    
    def get_work_data(self) -> dict:
        """Получить данные работы из формы."""
        # Проверка обязательных полей
        if not self.work_name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Наименование работы обязательно для заполнения")
            return None
        
        if self.planned_spin.value() <= 0:
            QMessageBox.warning(self, "Ошибка", "Плановый объём должен быть больше 0")
            return None
        
        # Определение скрытой работы
        hidden_index = self.hidden_combo.currentIndex()
        if hidden_index == 0:
            hidden_work = False
        elif hidden_index == 1:
            hidden_work = True
        else:
            hidden_work = False  # Для смешанных работ пока false
        
        return {
            "project_id": self.project_id,
            "vor_number": self.vor_number_edit.text().strip(),
            "section": "",
            "subsection": "",
            "work_name": self.work_name_edit.text().strip(),
            "unit": self.unit_combo.currentText(),
            "planned_quantity": self.planned_spin.value(),
            "actual_quantity": self.work_item.actual_quantity if self.work_item else 0,
            "location": self.location_edit.text().strip(),
            "floor": self.floor_edit.text().strip(),
            "axis": self.axis_edit.text().strip(),
            "elevation": self.elevation_edit.text().strip(),
            "material": self.material_edit.text().strip(),
            "hidden_work": hidden_work,
            "work_type": self.work_type_combo.currentText(),
            "predecessor_work_id": None,
            "successor_work_id": None,
            "project_document": self.project_doc_edit.text().strip(),
            "drawing_number": self.drawing_edit.text().strip(),
            "normative_documents": self.normative_edit.toPlainText().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
            "status": self.work_item.status if self.work_item else "planned"
        }
