"""
Виджет информации о проекте.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QGroupBox,
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt

from app.database.models.models import Project
from app.database.repositories import (
    ProjectRepository, OrganizationRepository,
    RepresentativeRepository, PersonRepository
)


class ProjectInfoWidget(QWidget):
    """Виджет отображения информации о проекте."""
    
    def __init__(self):
        super().__init__()
        
        self.current_project: Project = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Инициализация пользовательского интерфейса."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Scroll area
        from PySide6.QtWidgets import QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_widget)
        self.scroll_layout.setSpacing(15)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def load_project(self, project: Project):
        """Загрузить проект в виджет."""
        self.current_project = project
        
        # Очистка layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Основная информация
        main_group = self._create_info_group("📋 Основная информация")
        main_layout = main_group.layout()
        
        main_layout.addRow("Название", QLabel(f"<b>{project.name}</b>"))
        main_layout.addRow("Адрес", QLabel(project.address or "Не указан"))
        main_layout.addRow("Описание", QLabel(project.description or "Не указано"))
        
        self.scroll_layout.addWidget(main_group)
        
        # Договор
        contract_group = self._create_info_group("📄 Договор")
        contract_layout = contract_group.layout()
        
        contract_layout.addRow("Номер договора", QLabel(project.contract_number or "Не указан"))
        contract_layout.addRow("Дата договора", QLabel(
            project.contract_date.strftime("%d.%m.%Y") if project.contract_date else "Не указана"
        ))
        
        self.scroll_layout.addWidget(contract_group)
        
        # Участники
        participants_group = self._create_info_group("👥 Участники строительства")
        participants_layout = participants_group.layout()
        
        # Заказчик
        customer_name = self._get_organization_name(project.customer_id)
        participants_layout.addRow("Заказчик", QLabel(customer_name))
        
        # Подрядчик
        contractor_name = self._get_organization_name(project.contractor_id)
        participants_layout.addRow("Подрядчик", QLabel(contractor_name))
        
        # Проектировщик
        designer_name = self._get_organization_name(project.designer_id)
        participants_layout.addRow("Проектировщик", QLabel(designer_name))
        
        self.scroll_layout.addWidget(participants_group)
        
        # Представители
        reps_group = self._create_info_group("👔 Представители")
        reps_layout = reps_group.layout()
        
        representatives = RepresentativeRepository.get_by_project(project.id)
        
        if representatives:
            for rep in representatives:
                person = PersonRepository.get_by_id(rep.person_id)
                if person:
                    type_label = QLabel(f"<b>{rep.representative_type.capitalize()}:</b>")
                    name_label = QLabel(f"{person.full_name} ({person.position or 'Без должности'})")
                    reps_layout.addRow(type_label, name_label)
        else:
            reps_layout.addRow(QLabel("Представители не назначены"))
        
        # Кнопка добавления представителя
        add_rep_btn = QPushButton("+ Добавить представителя")
        add_rep_btn.clicked.connect(self._add_representative)
        reps_layout.addRow(add_rep_btn)
        
        self.scroll_layout.addWidget(reps_group)
        
        # Сроки
        dates_group = self._create_info_group("📅 Сроки выполнения")
        dates_layout = dates_group.layout()
        
        dates_layout.addRow("Дата начала", QLabel(
            project.start_date.strftime("%d.%m.%Y") if project.start_date else "Не указана"
        ))
        dates_layout.addRow("Дата окончания", QLabel(
            project.end_date.strftime("%d.%m.%Y") if project.end_date else "Не указана"
        ))
        
        self.scroll_layout.addWidget(dates_group)
        
        self.scroll_layout.addStretch()
    
    def _create_info_group(self, title: str) -> QGroupBox:
        """Создать группу информации."""
        group = QGroupBox(title)
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        group.setLayout(layout)
        return group
    
    def _get_organization_name(self, org_id: int) -> str:
        """Получить название организации по ID."""
        if not org_id:
            return "Не выбрано"
        
        org = OrganizationRepository.get_by_id(org_id)
        return org.name if org else "Не найдено"
    
    def _add_representative(self):
        """Добавить представителя."""
        from app.ui.representative_dialog import RepresentativeDialog
        
        if not self.current_project:
            return
        
        dialog = RepresentativeDialog(self, self.current_project.id)
        if dialog.exec():
            rep_data = dialog.get_representative_data()
            if rep_data:
                from app.database.models.models import Representative
                
                rep = Representative(**rep_data)
                rep_id = RepresentativeRepository.create(rep)
                
                if rep_id > 0:
                    QMessageBox.information(self, "Успешно", "Представитель добавлен")
                    self.load_project(self.current_project)
                else:
                    QMessageBox.critical(self, "Ошибка", "Не удалось добавить представителя")
