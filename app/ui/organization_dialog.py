"""
Диалог добавления организации.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt


class OrganizationDialog(QDialog):
    """Диалог добавления/редактирования организации."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Добавить организацию")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Форма
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Название
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("ООО 'СтройМонтаж'")
        form_layout.addRow("Название*", self.name_edit)
        
        # ИНН
        self.inn_edit = QLineEdit()
        self.inn_edit.setPlaceholderText("1234567890")
        self.inn_edit.setMaxLength(12)
        form_layout.addRow("ИНН", self.inn_edit)
        
        # ОГРН
        self.ogrn_edit = QLineEdit()
        self.ogrn_edit.setPlaceholderText("1234567890123")
        self.ogrn_edit.setMaxLength(13)
        form_layout.addRow("ОГРН", self.ogrn_edit)
        
        # Адрес
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText("г. Москва, ул. Строителей, д. 1")
        form_layout.addRow("Адрес", self.address_edit)
        
        # Телефон
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("+7 (XXX) XXX-XX-XX")
        form_layout.addRow("Телефон", self.phone_edit)
        
        # Email
        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("info@company.ru")
        form_layout.addRow("Email", self.email_edit)
        
        layout.addLayout(form_layout)
        
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
    
    def get_organization_data(self) -> dict:
        """Получить данные организации."""
        # Проверка обязательных полей
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название организации обязательно для заполнения")
            return None
        
        return {
            "name": self.name_edit.text().strip(),
            "inn": self.inn_edit.text().strip(),
            "ogrn": self.ogrn_edit.text().strip(),
            "address": self.address_edit.text().strip(),
            "phone": self.phone_edit.text().strip(),
            "email": self.email_edit.text().strip()
        }
