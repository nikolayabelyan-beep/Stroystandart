"""
Диалог создания/редактирования проекта.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QDateEdit, QPushButton, QLabel,
    QComboBox, QMessageBox, QGroupBox, QWidget, QScrollArea
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from app.database.models.models import Project
from app.database.repositories import OrganizationRepository


class ProjectDialog(QDialog):
    """Диалог создания/редактирования проекта."""
    
    def __init__(self, parent=None, project: Project = None):
        super().__init__(parent)
        
        self.project = project
        self.is_edit = project is not None
        
        if self.is_edit:
            self.setWindowTitle("Редактирование объекта")
        else:
            self.setWindowTitle("Новый объект")
        
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)
        
        self._init_ui()
        
        if self.is_edit:
            self._load_project_data()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Scroll area для возможности прокрутки
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # Основная информация
        main_group = QGroupBox("📋 Основная информация")
        main_layout = QFormLayout()
        main_layout.setSpacing(10)
        
        # Название
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Жилой комплекс 'Северный'")
        main_layout.addRow("Название*", self.name_edit)
        
        # Адрес
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("Полный адрес объекта")
        main_layout.addRow("Адрес", self.address_edit)
        
        # Описание
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Краткое описание объекта")
        main_layout.addRow("Описание", self.description_edit)
        
        main_group.setLayout(main_layout)
        scroll_layout.addWidget(main_group)
        
        # Договор
        contract_group = QGroupBox("📄 Договор")
        contract_layout = QFormLayout()
        contract_layout.setSpacing(10)
        
        # Номер договора
        self.contract_number_edit = QLineEdit()
        self.contract_number_edit.setPlaceholderText("Например: 123-ПК")
        contract_layout.addRow("Номер договора", self.contract_number_edit)
        
        # Дата договора
        self.contract_date_edit = QDateEdit()
        self.contract_date_edit.setCalendarPopup(True)
        self.contract_date_edit.setDate(QDate.currentDate())
        contract_layout.addRow("Дата договора", self.contract_date_edit)
        
        contract_group.setLayout(contract_layout)
        scroll_layout.addWidget(contract_group)
        
        # Участники
        participants_group = QGroupBox("👥 Участники строительства")
        participants_layout = QFormLayout()
        participants_layout.setSpacing(10)
        
        # Заказчик
        self.customer_combo = QComboBox()
        self.customer_combo.addItem("Не выбрано", None)
        self._load_organizations(self.customer_combo)
        participants_layout.addRow("Заказчик", self.customer_combo)
        
        # Подрядчик
        self.contractor_combo = QComboBox()
        self.contractor_combo.addItem("Не выбрано", None)
        self._load_organizations(self.contractor_combo)
        participants_layout.addRow("Подрядчик", self.contractor_combo)
        
        # Проектировщик
        self.designer_combo = QComboBox()
        self.designer_combo.addItem("Не выбрано", None)
        self._load_organizations(self.designer_combo)
        participants_layout.addRow("Проектировщик", self.designer_combo)
        
        participants_group.setLayout(participants_layout)
        scroll_layout.addWidget(participants_group)
        
        # Сроки
        dates_group = QGroupBox("📅 Сроки выполнения")
        dates_layout = QFormLayout()
        dates_layout.setSpacing(10)
        
        # Дата начала
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate())
        dates_layout.addRow("Дата начала", self.start_date_edit)
        
        # Дата окончания
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate().addDays(365))
        dates_layout.addRow("Дата окончания", self.end_date_edit)
        
        dates_group.setLayout(dates_layout)
        scroll_layout.addWidget(dates_group)
        
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
    
    def _load_organizations(self, combo: QComboBox):
        """Загрузить организации в комбобокс."""
        organizations = OrganizationRepository.get_all()
        
        for org in organizations:
            combo.addItem(org.name, org.id)
    
    def _load_project_data(self):
        """Загрузить данные проекта в форму."""
        if not self.project:
            return
        
        self.name_edit.setText(self.project.name)
        self.address_edit.setText(self.project.address)
        self.description_edit.setText(self.project.description or "")
        
        self.contract_number_edit.setText(self.project.contract_number or "")
        if self.project.contract_date:
            self.contract_date_edit.setDate(QDate.fromString(self.project.contract_date.isoformat(), "yyyy-MM-dd"))
        
        # Выбор организаций
        self._select_organization(self.customer_combo, self.project.customer_id)
        self._select_organization(self.contractor_combo, self.project.contractor_id)
        self._select_organization(self.designer_combo, self.project.designer_id)
        
        if self.project.start_date:
            self.start_date_edit.setDate(QDate.fromString(self.project.start_date.isoformat(), "yyyy-MM-dd"))
        if self.project.end_date:
            self.end_date_edit.setDate(QDate.fromString(self.project.end_date.isoformat(), "yyyy-MM-dd"))
    
    def _select_organization(self, combo: QComboBox, org_id: int):
        """Выбрать организацию в комбобоксе."""
        if not org_id:
            return
        
        for i in range(combo.count()):
            if combo.itemData(i) == org_id:
                combo.setCurrentIndex(i)
                break
    
    def get_project_data(self) -> dict:
        """Получить данные проекта из формы."""
        # Проверка обязательных полей
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название объекта обязательно для заполнения")
            return None
        
        return {
            "name": self.name_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "contract_number": self.contract_number_edit.text().strip(),
            "contract_date": self.contract_date_edit.date().toPython(),
            "customer_id": self.customer_combo.currentData(),
            "contractor_id": self.contractor_combo.currentData(),
            "designer_id": self.designer_combo.currentData(),
            "start_date": self.start_date_edit.date().toPython(),
            "end_date": self.end_date_edit.date().toPython(),
            "description": self.description_edit.toPlainText().strip()
        }
