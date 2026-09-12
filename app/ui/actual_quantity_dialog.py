"""
Диалог ввода фактического объёма работы.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDoubleSpinBox, QPushButton, QLabel, QMessageBox
)
from PySide6.QtCore import Qt

from app.database.models.models import WorkItem


class ActualQuantityDialog(QDialog):
    """Диалог ввода фактического объёма."""
    
    def __init__(self, parent=None, work_item: WorkItem = None):
        super().__init__(parent)
        
        self.work_item = work_item
        
        self.setWindowTitle("Внести фактический объём")
        self.setMinimumWidth(400)
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Информация о работе
        info_label = QLabel(f"<b>{self.work_item.work_name}</b>")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Плановый объём
        plan_label = QLabel(f"Плановый объём: <b>{self.work_item.planned_quantity:.2f} {self.work_item.unit or 'ед.'}</b>")
        layout.addWidget(plan_label)
        
        # Текущий факт
        current_actual = self.work_item.actual_quantity or 0
        actual_label = QLabel(f"Текущий фактический объём: <b>{current_actual:.2f} {self.work_item.unit or 'ед.'}</b>")
        layout.addWidget(actual_label)
        
        # Остаток
        remaining = self.work_item.planned_quantity - current_actual
        remaining_label = QLabel(f"Остаток: <b>{remaining:.2f} {self.work_item.unit or 'ед.'}</b>")
        if remaining > 0:
            remaining_label.setStyleSheet("color: #FF9800;")
        elif remaining < 0:
            remaining_label.setStyleSheet("color: #F44336;")
        else:
            remaining_label.setStyleSheet("color: #4CAF50;")
        layout.addWidget(remaining_label)
        
        # Форма ввода
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Фактический объём
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setRange(0, 999999)
        self.quantity_spin.setDecimals(2)
        self.quantity_spin.setValue(current_actual)
        self.quantity_spin.setSuffix(f" {self.work_item.unit or ''}")
        
        form_layout.addRow("Фактический объём*", self.quantity_spin)
        
        layout.addLayout(form_layout)
        
        # Предупреждение о превышении
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet("color: #F44336; font-weight: bold;")
        self.warning_label.setWordWrap(True)
        layout.addWidget(self.warning_label)
        
        self.quantity_spin.valueChanged.connect(self._check_exceeding)
        self._check_exceeding(current_actual)
        
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
    
    def _check_exceeding(self, value: float):
        """Проверить превышение планового объёма."""
        if value > self.work_item.planned_quantity:
            excess = value - self.work_item.planned_quantity
            self.warning_label.setText(
                f"⚠️ Превышение планового объёма на {excess:.2f} {self.work_item.unit or 'ед.'}!"
            )
        else:
            self.warning_label.setText("")
    
    def get_quantity(self) -> float:
        """Получить введённый объём."""
        return self.quantity_spin.value()
