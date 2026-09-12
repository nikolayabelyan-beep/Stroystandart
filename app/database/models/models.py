"""
Модели данных приложения.
ORM-подобные классы для работы с базой данных.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any


class Organization:
    """Модель организации."""
    
    def __init__(
        self,
        name: str,
        inn: str = "",
        ogrn: str = "",
        address: str = "",
        phone: str = "",
        email: str = "",
        id: Optional[int] = None
    ):
        self.id = id
        self.name = name
        self.inn = inn
        self.ogrn = ogrn
        self.address = address
        self.phone = phone
        self.email = email
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "inn": self.inn,
            "ogrn": self.ogrn,
            "address": self.address,
            "phone": self.phone,
            "email": self.email
        }
    
    @classmethod
    def from_row(cls, row: Any) -> 'Organization':
        """Создать из строки базы данных."""
        org = cls(
            id=row["id"],
            name=row["name"],
            inn=row["inn"] or "",
            ogrn=row["ogrn"] or "",
            address=row["address"] or "",
            phone=row["phone"] or "",
            email=row["email"] or ""
        )
        if row["created_at"]:
            org.created_at = datetime.fromisoformat(row["created_at"])
        if row["updated_at"]:
            org.updated_at = datetime.fromisoformat(row["updated_at"])
        return org


class Person:
    """Модель персоны."""
    
    def __init__(
        self,
        full_name: str,
        position: str = "",
        organization_id: Optional[int] = None,
        order_number: str = "",
        order_date: Optional[date] = None,
        nrs_number: str = "",
        phone: str = "",
        email: str = "",
        id: Optional[int] = None
    ):
        self.id = id
        self.full_name = full_name
        self.position = position
        self.organization_id = organization_id
        self.order_number = order_number
        self.order_date = order_date
        self.nrs_number = nrs_number
        self.phone = phone
        self.email = email
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "full_name": self.full_name,
            "position": self.position,
            "organization_id": self.organization_id,
            "order_number": self.order_number,
            "order_date": self.order_date.isoformat() if self.order_date else None,
            "nrs_number": self.nrs_number,
            "phone": self.phone,
            "email": self.email
        }
    
    @classmethod
    def from_row(cls, row: Any) -> 'Person':
        """Создать из строки базы данных."""
        person = cls(
            id=row["id"],
            full_name=row["full_name"],
            position=row["position"] or "",
            organization_id=row["organization_id"],
            order_number=row["order_number"] or "",
            nrs_number=row["nrs_number"] or "",
            phone=row["phone"] or "",
            email=row["email"] or ""
        )
        if row["order_date"]:
            person.order_date = date.fromisoformat(row["order_date"])
        if row["created_at"]:
            person.created_at = datetime.fromisoformat(row["created_at"])
        if row["updated_at"]:
            person.updated_at = datetime.fromisoformat(row["updated_at"])
        return person


class Project:
    """Модель проекта (объекта)."""
    
    def __init__(
        self,
        name: str,
        address: str = "",
        contract_number: str = "",
        contract_date: Optional[date] = None,
        customer_id: Optional[int] = None,
        contractor_id: Optional[int] = None,
        designer_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        description: str = "",
        id: Optional[int] = None
    ):
        self.id = id
        self.name = name
        self.address = address
        self.contract_number = contract_number
        self.contract_date = contract_date
        self.customer_id = customer_id
        self.contractor_id = contractor_id
        self.designer_id = designer_id
        self.start_date = start_date
        self.end_date = end_date
        self.description = description
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "contract_number": self.contract_number,
            "contract_date": self.contract_date.isoformat() if self.contract_date else None,
            "customer_id": self.customer_id,
            "contractor_id": self.contractor_id,
            "designer_id": self.designer_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description
        }
    
    @classmethod
    def from_row(cls, row: Any) -> 'Project':
        """Создать из строки базы данных."""
        project = cls(
            id=row["id"],
            name=row["name"],
            address=row["address"] or "",
            contract_number=row["contract_number"] or "",
            customer_id=row["customer_id"],
            contractor_id=row["contractor_id"],
            designer_id=row["designer_id"],
            description=row["description"] or ""
        )
        if row["contract_date"]:
            project.contract_date = date.fromisoformat(row["contract_date"])
        if row["start_date"]:
            project.start_date = date.fromisoformat(row["start_date"])
        if row["end_date"]:
            project.end_date = date.fromisoformat(row["end_date"])
        if row["created_at"]:
            project.created_at = datetime.fromisoformat(row["created_at"])
        if row["updated_at"]:
            project.updated_at = datetime.fromisoformat(row["updated_at"])
        return project


class Representative:
    """Модель представителя."""
    
    REPRESENTATIVE_TYPES = [
        "заказчик",
        "строительный контроль заказчика",
        "подрядчик",
        "строительный контроль подрядчика",
        "проектировщик",
        "исполнитель работ"
    ]
    
    def __init__(
        self,
        project_id: int,
        person_id: int,
        representative_type: str,
        id: Optional[int] = None
    ):
        self.id = id
        self.project_id = project_id
        self.person_id = person_id
        self.representative_type = representative_type
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "person_id": self.person_id,
            "representative_type": self.representative_type
        }
    
    @classmethod
    def from_row(cls, row: Any) -> 'Representative':
        """Создать из строки базы данных."""
        rep = cls(
            id=row["id"],
            project_id=row["project_id"],
            person_id=row["person_id"],
            representative_type=row["representative_type"]
        )
        if row["created_at"]:
            rep.created_at = datetime.fromisoformat(row["created_at"])
        if row["updated_at"]:
            rep.updated_at = datetime.fromisoformat(row["updated_at"])
        return rep


class WorkItem:
    """Модель элемента ВОР."""
    
    STATUSES = [
        "planned",           # Запланировано
        "in_progress",       # В работе
        "completed",         # Выполнено
        "verified",          # Проверено
        "approved"           # Согласовано
    ]
    
    WORK_TYPES = [
        "Земляные работы",
        "Фундаменты",
        "Стены",
        "Перекрытия",
        "Кровля",
        "Фасадные работы",
        "Отделочные работы",
        "Инженерные системы",
        "Благоустройство"
    ]
    
    def __init__(
        self,
        project_id: int,
        work_name: str,
        vor_number: str = "",
        section: str = "",
        subsection: str = "",
        unit: str = "",
        planned_quantity: float = 0.0,
        actual_quantity: float = 0.0,
        location: str = "",
        floor: str = "",
        axis: str = "",
        elevation: str = "",
        material: str = "",
        hidden_work: bool = False,
        work_type: str = "",
        predecessor_work_id: Optional[int] = None,
        successor_work_id: Optional[int] = None,
        project_document: str = "",
        drawing_number: str = "",
        normative_documents: str = "",
        notes: str = "",
        status: str = "planned",
        id: Optional[int] = None
    ):
        self.id = id
        self.project_id = project_id
        self.vor_number = vor_number
        self.section = section
        self.subsection = subsection
        self.work_name = work_name
        self.unit = unit
        self.planned_quantity = planned_quantity
        self.actual_quantity = actual_quantity
        self.remaining_quantity = planned_quantity - actual_quantity
        self.location = location
        self.floor = floor
        self.axis = axis
        self.elevation = elevation
        self.material = material
        self.hidden_work = hidden_work
        self.work_type = work_type
        self.predecessor_work_id = predecessor_work_id
        self.successor_work_id = successor_work_id
        self.project_document = project_document
        self.drawing_number = drawing_number
        self.normative_documents = normative_documents
        self.notes = notes
        self.status = status
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def update_quantities(self):
        """Обновить остаток после изменения объёмов."""
        self.remaining_quantity = self.planned_quantity - self.actual_quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "vor_number": self.vor_number,
            "section": self.section,
            "subsection": self.subsection,
            "work_name": self.work_name,
            "unit": self.unit,
            "planned_quantity": self.planned_quantity,
            "actual_quantity": self.actual_quantity,
            "remaining_quantity": self.remaining_quantity,
            "location": self.location,
            "floor": self.floor,
            "axis": self.axis,
            "elevation": self.elevation,
            "material": self.material,
            "hidden_work": self.hidden_work,
            "work_type": self.work_type,
            "predecessor_work_id": self.predecessor_work_id,
            "successor_work_id": self.successor_work_id,
            "project_document": self.project_document,
            "drawing_number": self.drawing_number,
            "normative_documents": self.normative_documents,
            "notes": self.notes,
            "status": self.status
        }
    
    @classmethod
    def from_row(cls, row: Any) -> 'WorkItem':
        """Создать из строки базы данных."""
        item = cls(
            id=row["id"],
            project_id=row["project_id"],
            vor_number=row["vor_number"] or "",
            section=row["section"] or "",
            subsection=row["subsection"] or "",
            work_name=row["work_name"],
            unit=row["unit"] or "",
            planned_quantity=row["planned_quantity"] or 0.0,
            actual_quantity=row["actual_quantity"] or 0.0,
            location=row["location"] or "",
            floor=row["floor"] or "",
            axis=row["axis"] or "",
            elevation=row["elevation"] or "",
            material=row["material"] or "",
            hidden_work=bool(row["hidden_work"]),
            work_type=row["work_type"] or "",
            predecessor_work_id=row["predecessor_work_id"],
            successor_work_id=row["successor_work_id"],
            project_document=row["project_document"] or "",
            drawing_number=row["drawing_number"] or "",
            normative_documents=row["normative_documents"] or "",
            notes=row["notes"] or "",
            status=row["status"] or "planned"
        )
        item.update_quantities()
        if row["created_at"]:
            item.created_at = datetime.fromisoformat(row["created_at"])
        if row["updated_at"]:
            item.updated_at = datetime.fromisoformat(row["updated_at"])
        return item


class Document:
    """Модель документа."""
    
    DOCUMENT_TYPES = [
        "АОСР",
        "Исполнительная схема",
        "Сертификат",
        "Паспорт",
        "Протокол испытаний",
        "Акт ввода в эксплуатацию",
        "КС-2",
        "КС-3",
        "Реестр ИД"
    ]
    
    STATUSES = [
        "draft",              # Черновик
        "requires_review",    # Требует проверки
        "ready",              # Готово
        "approved",           # Подписано
        "submitted"           # Передано заказчику
    ]
    
    def __init__(
        self,
        project_id: int,
        document_type: str,
        work_item_id: Optional[int] = None,
        document_number: str = "",
        document_date: Optional[date] = None,
        file_path: str = "",
        status: str = "draft",
        generated_by_ai: bool = False,
        manually_edited: bool = False,
        id: Optional[int] = None
    ):
        self.id = id
        self.project_id = project_id
        self.work_item_id = work_item_id
        self.document_type = document_type
        self.document_number = document_number
        self.document_date = document_date
        self.file_path = file_path
        self.status = status
        self.generated_by_ai = generated_by_ai
        self.manually_edited = manually_edited
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь."""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "work_item_id": self.work_item_id,
            "document_type": self.document_type,
            "document_number": self.document_number,
            "document_date": self.document_date.isoformat() if self.document_date else None,
            "file_path": self.file_path,
            "status": self.status,
            "generated_by_ai": self.generated_by_ai,
            "manually_edited": self.manually_edited
        }
    
    @classmethod
    def from_row(cls, row: Any) -> 'Document':
        """Создать из строки базы данных."""
        doc = cls(
            id=row["id"],
            project_id=row["project_id"],
            work_item_id=row["work_item_id"],
            document_type=row["document_type"],
            document_number=row["document_number"] or "",
            file_path=row["file_path"] or "",
            status=row["status"] or "draft",
            generated_by_ai=bool(row["generated_by_ai"]),
            manually_edited=bool(row["manually_edited"])
        )
        if row["document_date"]:
            doc.document_date = date.fromisoformat(row["document_date"])
        if row["created_at"]:
            doc.created_at = datetime.fromisoformat(row["created_at"])
        if row["updated_at"]:
            doc.updated_at = datetime.fromisoformat(row["updated_at"])
        return doc
