"""
Репозитории для работы с базой данных.
CRUD операции для каждой модели.
"""
from typing import Optional, List, Dict, Any
from datetime import date

from app.database.db_manager import DatabaseManager
from app.database.models.models import (
    Organization, Person, Project, Representative,
    WorkItem, Document
)


class OrganizationRepository:
    """Репозиторий для организаций."""
    
    @staticmethod
    def create(org: Organization) -> int:
        """Создать организацию."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            INSERT INTO organizations (name, inn, ogrn, address, phone, email)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (org.name, org.inn, org.ogrn, org.address, org.phone, org.email)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(org_id: int) -> Optional[Organization]:
        """Получить организацию по ID."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM organizations WHERE id = ?",
            (org_id,)
        )
        row = cursor.fetchone()
        return Organization.from_row(row) if row else None
    
    @staticmethod
    def get_all() -> List[Organization]:
        """Получить все организации."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query("SELECT * FROM organizations ORDER BY name")
        return [Organization.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(org: Organization) -> bool:
        """Обновить организацию."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            UPDATE organizations
            SET name=?, inn=?, ogrn=?, address=?, phone=?, email=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (org.name, org.inn, org.ogrn, org.address, org.phone, org.email, org.id)
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(org_id: int) -> bool:
        """Удалить организацию."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "DELETE FROM organizations WHERE id = ?",
            (org_id,)
        )
        db.commit()
        return cursor.rowcount > 0


class PersonRepository:
    """Репозиторий для персон."""
    
    @staticmethod
    def create(person: Person) -> int:
        """Создать персону."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            INSERT INTO persons (full_name, position, organization_id, order_number, order_date, nrs_number, phone, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (person.full_name, person.position, person.organization_id,
             person.order_number, person.order_date.isoformat() if person.order_date else None,
             person.nrs_number, person.phone, person.email)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(person_id: int) -> Optional[Person]:
        """Получить персону по ID."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM persons WHERE id = ?",
            (person_id,)
        )
        row = cursor.fetchone()
        return Person.from_row(row) if row else None
    
    @staticmethod
    def get_all() -> List[Person]:
        """Получить все персоны."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query("SELECT * FROM persons ORDER BY full_name")
        return [Person.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(person: Person) -> bool:
        """Обновить персону."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            UPDATE persons
            SET full_name=?, position=?, organization_id=?, order_number=?, order_date=?, nrs_number=?, phone=?, email=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (person.full_name, person.position, person.organization_id,
             person.order_number, person.order_date.isoformat() if person.order_date else None,
             person.nrs_number, person.phone, person.email, person.id)
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(person_id: int) -> bool:
        """Удалить персону."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "DELETE FROM persons WHERE id = ?",
            (person_id,)
        )
        db.commit()
        return cursor.rowcount > 0


class ProjectRepository:
    """Репозиторий для проектов."""
    
    @staticmethod
    def create(project: Project) -> int:
        """Создать проект."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            INSERT INTO projects (name, address, contract_number, contract_date, customer_id, contractor_id, designer_id, start_date, end_date, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project.name, project.address, project.contract_number,
             project.contract_date.isoformat() if project.contract_date else None,
             project.customer_id, project.contractor_id, project.designer_id,
             project.start_date.isoformat() if project.start_date else None,
             project.end_date.isoformat() if project.end_date else None,
             project.description)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(project_id: int) -> Optional[Project]:
        """Получить проект по ID."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        return Project.from_row(row) if row else None
    
    @staticmethod
    def get_all() -> List[Project]:
        """Получить все проекты."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query("SELECT * FROM projects ORDER BY name")
        return [Project.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(project: Project) -> bool:
        """Обновить проект."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            UPDATE projects
            SET name=?, address=?, contract_number=?, contract_date=?, customer_id=?, contractor_id=?, designer_id=?, start_date=?, end_date=?, description=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (project.name, project.address, project.contract_number,
             project.contract_date.isoformat() if project.contract_date else None,
             project.customer_id, project.contractor_id, project.designer_id,
             project.start_date.isoformat() if project.start_date else None,
             project.end_date.isoformat() if project.end_date else None,
             project.description, project.id)
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(project_id: int) -> bool:
        """Удалить проект."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "DELETE FROM projects WHERE id = ?",
            (project_id,)
        )
        db.commit()
        return cursor.rowcount > 0


class RepresentativeRepository:
    """Репозиторий для представителей."""
    
    @staticmethod
    def create(rep: Representative) -> int:
        """Создать представителя."""
        db = DatabaseManager.get_instance()
        try:
            cursor = db.execute_query(
                """
                INSERT INTO representatives (project_id, person_id, representative_type)
                VALUES (?, ?, ?)
                """,
                (rep.project_id, rep.person_id, rep.representative_type)
            )
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Ошибка при создании представителя: {e}")
            return -1
    
    @staticmethod
    def get_by_project(project_id: int) -> List[Representative]:
        """Получить всех представителей проекта."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM representatives WHERE project_id = ?",
            (project_id,)
        )
        return [Representative.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def delete(rep_id: int) -> bool:
        """Удалить представителя."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "DELETE FROM representatives WHERE id = ?",
            (rep_id,)
        )
        db.commit()
        return cursor.rowcount > 0


class WorkItemRepository:
    """Репозиторий для элементов ВОР."""
    
    @staticmethod
    def create(item: WorkItem) -> int:
        """Создать элемент ВОР."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            INSERT INTO work_items (project_id, vor_number, section, subsection, work_name, unit, planned_quantity, actual_quantity, remaining_quantity, location, floor, axis, elevation, material, hidden_work, work_type, predecessor_work_id, successor_work_id, project_document, drawing_number, normative_documents, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (item.project_id, item.vor_number, item.section, item.subsection,
             item.work_name, item.unit, item.planned_quantity, item.actual_quantity,
             item.remaining_quantity, item.location, item.floor, item.axis,
             item.elevation, item.material, item.hidden_work, item.work_type,
             item.predecessor_work_id, item.successor_work_id, item.project_document,
             item.drawing_number, item.normative_documents, item.notes, item.status)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(item_id: int) -> Optional[WorkItem]:
        """Получить элемент ВОР по ID."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM work_items WHERE id = ?",
            (item_id,)
        )
        row = cursor.fetchone()
        return WorkItem.from_row(row) if row else None
    
    @staticmethod
    def get_by_project(project_id: int) -> List[WorkItem]:
        """Получить все элементы ВОР проекта."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM work_items WHERE project_id = ? ORDER BY vor_number",
            (project_id,)
        )
        return [WorkItem.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(item: WorkItem) -> bool:
        """Обновить элемент ВОР."""
        db = DatabaseManager.get_instance()
        item.update_quantities()
        cursor = db.execute_query(
            """
            UPDATE work_items
            SET vor_number=?, section=?, subsection=?, work_name=?, unit=?, planned_quantity=?, actual_quantity=?, remaining_quantity=?, location=?, floor=?, axis=?, elevation=?, material=?, hidden_work=?, work_type=?, predecessor_work_id=?, successor_work_id=?, project_document=?, drawing_number=?, normative_documents=?, notes=?, status=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (item.vor_number, item.section, item.subsection, item.work_name,
             item.unit, item.planned_quantity, item.actual_quantity, item.remaining_quantity,
             item.location, item.floor, item.axis, item.elevation, item.material,
             item.hidden_work, item.work_type, item.predecessor_work_id,
             item.successor_work_id, item.project_document, item.drawing_number,
             item.normative_documents, item.notes, item.status, item.id)
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(item_id: int) -> bool:
        """Удалить элемент ВОР."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "DELETE FROM work_items WHERE id = ?",
            (item_id,)
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def bulk_insert(items: List[WorkItem]) -> int:
        """Массовая вставка элементов ВОР."""
        if not items:
            return 0
        
        db = DatabaseManager.get_instance()
        cursor = db.get_connection().cursor()
        
        count = 0
        for item in items:
            try:
                cursor.execute(
                    """
                    INSERT INTO work_items (project_id, vor_number, section, subsection, work_name, unit, planned_quantity, actual_quantity, remaining_quantity, location, floor, axis, elevation, material, hidden_work, work_type, predecessor_work_id, successor_work_id, project_document, drawing_number, normative_documents, notes, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (item.project_id, item.vor_number, item.section, item.subsection,
                     item.work_name, item.unit, item.planned_quantity, item.actual_quantity,
                     item.remaining_quantity, item.location, item.floor, item.axis,
                     item.elevation, item.material, item.hidden_work, item.work_type,
                     item.predecessor_work_id, item.successor_work_id, item.project_document,
                     item.drawing_number, item.normative_documents, item.notes, item.status)
                )
                count += 1
            except Exception as e:
                print(f"Ошибка при вставке элемента {item.work_name}: {e}")
        
        db.commit()
        cursor.close()
        return count


class DocumentRepository:
    """Репозиторий для документов."""
    
    @staticmethod
    def create(doc: Document) -> int:
        """Создать документ."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            INSERT INTO documents (project_id, work_item_id, document_type, document_number, document_date, file_path, status, generated_by_ai, manually_edited)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (doc.project_id, doc.work_item_id, doc.document_type,
             doc.document_number, doc.document_date.isoformat() if doc.document_date else None,
             doc.file_path, doc.status, doc.generated_by_ai, doc.manually_edited)
        )
        db.commit()
        return cursor.lastrowid
    
    @staticmethod
    def get_by_id(doc_id: int) -> Optional[Document]:
        """Получить документ по ID."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,)
        )
        row = cursor.fetchone()
        return Document.from_row(row) if row else None
    
    @staticmethod
    def get_by_project(project_id: int) -> List[Document]:
        """Получить все документы проекта."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM documents WHERE project_id = ? ORDER BY document_date DESC",
            (project_id,)
        )
        return [Document.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_by_work_item(work_item_id: int) -> List[Document]:
        """Получить все документы работы."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "SELECT * FROM documents WHERE work_item_id = ? ORDER BY document_type",
            (work_item_id,)
        )
        return [Document.from_row(row) for row in cursor.fetchall()]
    
    @staticmethod
    def update(doc: Document) -> bool:
        """Обновить документ."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            """
            UPDATE documents
            SET work_item_id=?, document_type=?, document_number=?, document_date=?, file_path=?, status=?, generated_by_ai=?, manually_edited=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (doc.work_item_id, doc.document_type, doc.document_number,
             doc.document_date.isoformat() if doc.document_date else None,
             doc.file_path, doc.status, doc.generated_by_ai, doc.manually_edited, doc.id)
        )
        db.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def delete(doc_id: int) -> bool:
        """Удалить документ."""
        db = DatabaseManager.get_instance()
        cursor = db.execute_query(
            "DELETE FROM documents WHERE id = ?",
            (doc_id,)
        )
        db.commit()
        return cursor.rowcount > 0
