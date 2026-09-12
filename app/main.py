"""
Точка входа приложения.
Запуск главного окна приложения.
"""
import sys
import os

# Добавляем корень приложения в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTranslator, QLocale
from PySide6.QtGui import QFont

from app.ui.main_window import MainWindow
from app.database.db_manager import DatabaseManager


def main():
    """Основная функция запуска приложения."""
    # Инициализация приложения
    app = QApplication(sys.argv)
    
    # Настройка приложения
    app.setApplicationName("СтройДокумент")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("StroyStandart")
    
    # Настройка шрифта
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Инициализация базы данных
    db_manager = DatabaseManager.get_instance()
    db_manager.initialize()
    
    # Создание и показ главного окна
    window = MainWindow()
    window.show()
    
    # Запуск цикла событий
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
