"""
Диалог добавления представителя.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel, QMessageBox,
    QDateEdit, QGroupBox, QWidget, QScrollArea
)
from PySide6.QtCore import Qt, QDate

from app.database.models.models import Representative
from app.database.repositories import PersonRepository, OrganizationRepository


class RepresentativeDialog(QDialog):
    """Диалог добавления/редактирования представителя."""
    
    def __init__(self, parent=None, project_id: int = None):
        super().__init__(parent)
        
        self.project_id = project_id
        
        self.setWindowTitle("Добавить представителя")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)
        
        self._init_ui()
    
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
        
        # Информация о персоне
        person_group = QGroupBox("👔 Информация о представителе")
        person_form = QFormLayout()
        person_form.setSpacing(10)
        
        # ФИО
        self.full_name_edit = QLineEdit()
        self.full_name_edit.setPlaceholderText("Иванов Иван Иванович")
        person_form.addRow("ФИО*", self.full_name_edit)
        
        # Должность
        self.position_edit = QLineEdit()
        self.position_edit.setPlaceholderText("Главный инженер")
        person_form.addRow("Должность", self.position_edit)
        
        # Организация
        self.org_combo = QComboBox()
        self.org_combo.addItem("Создать новую...", None)
        self._load_organizations()
        person_form.addRow("Организация", self.org_combo)
        self.org_combo.currentIndexChanged.connect(self._on_org_changed)
        
        # Телефон
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (XXX) XXX-XX-XX")
        person_form.addRow("Телефон", self.phone_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("email@example.com")
        person_form.addRow("Email", self.email_edit)
        
        person_group.setLayout(person_form)
        scroll_layout.addWidget(person_group)
        
        # Основание полномочий
        authority_group = QGroupBox("📄 Основание полномочий")
        authority_form = QFormLayout()
        authority_form.setSpacing(10)
        
        # Номер приказа
        self.order_number_edit = QLineEdit()
        self.order_number_edit.setPlaceholderText("123-к")
        authority_form.addRow("Номер приказа", self.order_number_edit)
        
        # Дата приказа
        self.order_date_edit = QDateEdit()
        self.order_date_edit.setCalendarPopup(True)
        self.order_date_edit.setDate(QDate.currentDate())
        authority_form.addRow("Дата приказа", self.order_date_edit)
        
        # Номер НРС
        self.nrs_edit = QLineEdit()
        self.nrs_edit.setPlaceholderText("НОПРИЗ/ГП/...")
        authority_form.addRow("Номер НРС", self.nrs_edit)
        
        authority_group.setLayout(authority_form)
        scroll_layout.addWidget(authority_group)
        
        # Тип представителя
        type_group = QGroupBox("🏷️ Тип представителя")
        type_form = QFormLayout()
        
        self.type_combo = QComboBox()
        for rep_type in Representative.REPRESENTATIVE_TYPES:
            self.type_combo.addItem(rep_type.capitalize(), rep_type)
        type_form.addRow("Роль в проекте", self.type_combo)
        
        type_group.setLayout(type_form)
        scroll_layout.addWidget(type_group)
        
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
    
    def _load_organizations(self):
        """Загрузить организации в комбобокс."""
        organizations = OrganizationRepository.get_all()
        
        for org in organizations:
            self.org_combo.addItem(org.name, org.id)
    
    def _on_org_changed(self, index: int):
        """Обработчик изменения организации."""
        if index == 0:  # "Создать новую..."
            from app.ui.organization_dialog import OrganizationDialog
            
            dialog = OrganizationDialog(self)
            if dialog.exec():
                org_data = dialog.get_organization_data()
                if org_data:
                    from app.database.models.models import Organization
                    
                    org = Organization(**org_data)
                    org_id = OrganizationRepository.create(org)
                    
                    if org_id > 0:
                        # Перезагрузка списка
                        self.org_combo.clear()
                        self.org_combo.addItem("Создать новую...", None)
                        self._load_organizations()
                        
                        # Выбор созданной организации
                        for i in range(self.org_combo.count()):
                            if self.org_combo.itemData(i) == org_id:
                                self.org_combo.setCurrentIndex(i)
                                break
    
    def get_representative_data(self) -> dict:
        """Получить данные представителя."""
        # Проверка обязательных полей
        if not self.full_name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "ФИО обязательно для заполнения")
            return None
        
        # Создание или получение персоны
        org_id = self.org_combo.currentData()
        
        person_data = {
            "full_name": self.full_name_edit.text().strip(),
            "position": self.position_edit.text().strip(),
            "organization_id": org_id,
            "order_number": self.order_number_edit.text().strip(),
            "order_date": self.order_date_edit.date().toPython(),
            "nrs_number": self.nrs_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip()
        }
        
        from app.database.models.models import Person
        person = Person(**person_data)
        person_id = PersonRepository.create(person)
        
        if person_id <= 0:
            QMessageBox.critical(self, "Ошибка", "Не удалось создать персону")
            return None
        
        return {
            "project_id": self.project_id,
            "person_id": person_id,
            "representative_type": self.type_combo.currentData()
        }
