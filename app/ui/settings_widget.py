"""
Виджет настроек приложения.
Настройки локального ИИ и общие параметры.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QPushButton,
    QLabel, QGroupBox, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt

import json
from pathlib import Path


class SettingsWidget(QWidget):
    """Виджет настроек приложения."""
    
    def __init__(self):
        super().__init__()
        
        self._init_ui()
        self._load_settings()
    
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
        
        # Настройки ИИ
        ai_group = QGroupBox("🤖 Локальный ИИ (Ollama/llama.cpp)")
        ai_form = QFormLayout()
        ai_form.setSpacing(10)
        
        # URL сервера
        self.ai_url_edit = QLineEdit()
        self.ai_url_edit.setPlaceholderText("http://127.0.0.1:11434")
        self.ai_url_edit.setToolTip("Адрес локального AI сервера")
        ai_form.addRow("URL сервера", self.ai_url_edit)
        
        # Модель
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        models = [
            "llama3.2",
            "llama3.1",
            "mistral",
            "gemma2",
            "qwen2.5",
            "phi3"
        ]
        for model in models:
            self.model_combo.addItem(model)
        self.model_combo.setToolTip("Модель для использования")
        ai_form.addRow("Модель", self.model_combo)
        
        # Температура
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setDecimals(2)
        self.temp_spin.setValue(0.7)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setToolTip("Температура генерации (0.0 - детерминировано, 2.0 - креативно)")
        ai_form.addRow("Температура", self.temp_spin)
        
        # Максимальный контекст
        self.context_spin = QDoubleSpinBox()
        self.context_spin.setRange(1024, 131072)
        self.context_spin.setDecimals(0)
        self.context_spin.setValue(8192)
        self.context_spin.setSingleStep(1024)
        self.context_spin.setToolTip("Максимальный размер контекста в токенах")
        ai_form.addRow("Макс. контекст", self.context_spin)
        
        # Режим JSON
        self.json_mode_combo = QComboBox()
        self.json_mode_combo.addItem("Включён", True)
        self.json_mode_combo.addItem("Выключен", False)
        self.json_mode_combo.setToolTip("Требовать JSON-ответы от модели")
        ai_form.addRow("JSON режим", self.json_mode_combo)
        
        ai_group.setLayout(ai_form)
        scroll_layout.addWidget(ai_group)
        
        # Системный промпт
        prompt_group = QGroupBox("📝 Системный промпт ИИ")
        prompt_layout = QVBoxLayout()
        
        from PySide6.QtWidgets import QTextEdit
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setMinimumHeight(200)
        self.prompt_edit.setPlaceholderText(
            "Ты — профессиональный помощник в области строительной исполнительной документации.\n"
            "Твоя задача — помогать пользователям классифицировать работы, подбирать нормативы, "
            "формировать акты АОСР и исполнительные схемы.\n\n"
            "ВАЖНО:\n"
            "- Никогда не выдумывай факты (ФИО, даты, номера документов, объёмы)\n"
            "- Если данных нет — пиши 'ДАННЫЕ НЕ ПРЕДОСТАВЛЕНЫ'\n"
            "- Отвечай только на основании предоставленной информации\n"
            "- Используй структурированный JSON для ответов"
        )
        prompt_layout.addWidget(self.prompt_edit)
        
        prompt_group.setLayout(prompt_layout)
        scroll_layout.addWidget(prompt_group)
        
        # Проверка подключения
        test_group = QGroupBox("🔌 Проверка подключения")
        test_layout = QHBoxLayout()
        
        test_label = QLabel("Проверьте доступность локального AI сервера")
        test_layout.addWidget(test_label)
        
        test_btn = QPushButton("Проверить подключение")
        test_btn.clicked.connect(self._test_connection)
        test_btn.setStyleSheet("""
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
        test_layout.addWidget(test_btn)
        
        test_group.setLayout(test_layout)
        scroll_layout.addWidget(test_group)
        
        # Сохранение
        save_group = QGroupBox("💾 Сохранение настроек")
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        reset_btn = QPushButton("Сбросить настройки")
        reset_btn.clicked.connect(self._reset_settings)
        reset_btn.setStyleSheet("""
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
        save_layout.addWidget(reset_btn)
        
        save_btn = QPushButton("Сохранить настройки")
        save_btn.clicked.connect(self._save_settings)
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
        save_layout.addWidget(save_btn)
        
        save_group.setLayout(save_layout)
        scroll_layout.addWidget(save_group)
        
        scroll_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def _get_settings_path(self) -> Path:
        """Получить путь к файлу настроек."""
        app_dir = Path(__file__).parent.parent.parent
        data_dir = app_dir / "data"
        data_dir.mkdir(exist_ok=True)
        return data_dir / "settings.json"
    
    def _load_settings(self):
        """Загрузить настройки из файла."""
        settings_path = self._get_settings_path()
        
        if not settings_path.exists():
            return
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            self.ai_url_edit.setText(settings.get('ai_url', 'http://127.0.0.1:11434'))
            
            model = settings.get('model', 'llama3.2')
            index = self.model_combo.findText(model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
            else:
                self.model_combo.setCurrentText(model)
            
            self.temp_spin.setValue(settings.get('temperature', 0.7))
            self.context_spin.setValue(settings.get('max_context', 8192))
            
            json_mode = settings.get('json_mode', True)
            self.json_mode_combo.setCurrentIndex(0 if json_mode else 1)
            
            self.prompt_edit.setText(settings.get('system_prompt', self.prompt_edit.toPlainText()))
            
        except Exception as e:
            print(f"Ошибка при загрузке настроек: {e}")
    
    def _save_settings(self):
        """Сохранить настройки в файл."""
        settings_path = self._get_settings_path()
        
        settings = {
            'ai_url': self.ai_url_edit.text().strip() or 'http://127.0.0.1:11434',
            'model': self.model_combo.currentText(),
            'temperature': self.temp_spin.value(),
            'max_context': int(self.context_spin.value()),
            'json_mode': self.json_mode_combo.currentData(),
            'system_prompt': self.prompt_edit.toPlainText()
        }
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(
                self,
                "Успешно",
                "Настройки сохранены"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось сохранить настройки:\n{e}"
            )
    
    def _reset_settings(self):
        """Сбросить настройки к значениям по умолчанию."""
        reply = QMessageBox.warning(
            self,
            "Подтверждение сброса",
            "Вы уверены, что хотите сбросить все настройки?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.ai_url_edit.setText("http://127.0.0.1:11434")
            self.model_combo.setCurrentText("llama3.2")
            self.temp_spin.setValue(0.7)
            self.context_spin.setValue(8192)
            self.json_mode_combo.setCurrentIndex(0)
            self.prompt_edit.setText(self.prompt_edit.placeholderText())
    
    def _test_connection(self):
        """Проверить подключение к AI серверу."""
        import requests
        
        url = self.ai_url_edit.text().strip() or 'http://127.0.0.1:11434'
        
        try:
            response = requests.get(f"{url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                QMessageBox.information(
                    self,
                    "Подключение успешно",
                    f"Сервер Ollama доступен!\n\n"
                    f"Доступные модели ({len(models)}):\n" +
                    "\n".join([m.get('name', 'unknown') for m in models[:10]])
                )
            else:
                QMessageBox.warning(
                    self,
                    "Ошибка подключения",
                    f"Сервер вернул статус: {response.status_code}"
                )
        except requests.exceptions.ConnectionError:
            QMessageBox.critical(
                self,
                "Ошибка подключения",
                f"Не удалось подключиться к серверу:\n{url}\n\n"
                "Убедитесь, что Ollama запущен."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Произошла ошибка:\n{e}"
            )
