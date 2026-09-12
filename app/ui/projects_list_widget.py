"""
Виджет списка проектов.
"""
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QMessageBox, QMenu
from PySide6.QtCore import Qt, Signal

from app.database.repositories import ProjectRepository
from app.database.models.models import Project


class ProjectsListWidget(QListWidget):
    """Виджет списка проектов."""
    
    project_selected = Signal(int)  # ID проекта
    
    def __init__(self):
        super().__init__()
        
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        self.setStyleSheet("""
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
    
    def load_projects(self):
        """Загрузить проекты из базы данных."""
        self.clear()
        
        projects = ProjectRepository.get_all()
        
        for project in projects:
            item = QListWidgetItem(f"🏗️ {project.name}")
            item.setData(Qt.UserRole, project.id)
            
            # Добавляем подсказку с адресом
            if project.address:
                item.setToolTip(f"{project.name}\n{project.address}")
            
            self.addItem(item)
    
    def _show_context_menu(self, position):
        """Показать контекстное меню."""
        item = self.itemAt(position)
        
        if not item:
            return
        
        project_id = item.data(Qt.UserRole)
        
        menu = QMenu(self)
        
        open_action = menu.addAction("📂 Открыть")
        open_action.triggered.connect(lambda: self._open_project(project_id))
        
        edit_action = menu.addAction("✏️ Редактировать")
        edit_action.triggered.connect(lambda: self._edit_project(project_id))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Удалить")
        delete_action.triggered.connect(lambda: self._delete_project(project_id))
        
        menu.exec_(self.viewport().mapToGlobal(position))
    
    def _open_project(self, project_id: int):
        """Открыть проект."""
        self.project_selected.emit(project_id)
    
    def _edit_project(self, project_id: int):
        """Редактировать проект."""
        project = ProjectRepository.get_by_id(project_id)
        
        if not project:
            return
        
        from app.ui.project_dialog import ProjectDialog
        
        dialog = ProjectDialog(self, project)
        if dialog.exec():
            updated_data = dialog.get_project_data()
            if updated_data:
                updated_data['id'] = project_id
                updated_project = Project(**updated_data)
                
                if ProjectRepository.update(updated_project):
                    self.load_projects()
                    QMessageBox.information(self, "Успешно", "Объект обновлён")
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось обновить объект")
    
    def _delete_project(self, project_id: int):
        """Удалить проект."""
        reply = QMessageBox.warning(
            self,
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить этот объект?\nВсе связанные данные будут удалены.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if ProjectRepository.delete(project_id):
                self.load_projects()
                QMessageBox.information(self, "Успешно", "Объект удалён")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось удалить объект")
