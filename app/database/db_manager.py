"""
Менеджер базы данных.
Управление подключением к SQLite и миграциями.
"""
import sqlite3
import os
from pathlib import Path
from typing import Optional


class DatabaseManager:
    """Одиночка для управления базой данных."""
    
    _instance: Optional['DatabaseManager'] = None
    _connection: Optional[sqlite3.Connection] = None
    
    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'DatabaseManager':
        """Получить экземпляр менеджера базы данных."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Инициализация менеджера базы данных."""
        if self._connection is not None:
            return
        
        # Определение пути к базе данных
        app_dir = Path(__file__).parent.parent.parent
        data_dir = app_dir / "data"
        data_dir.mkdir(exist_ok=True)
        
        self.db_path = data_dir / "stroydocument.db"
        
    def initialize(self) -> None:
        """Инициализация базы данных и создание таблиц."""
        self._connect()
        self._create_tables()
        self._enable_foreign_keys()
        
    def _connect(self) -> None:
        """Подключение к базе данных."""
        self._connection = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False
        )
        self._connection.row_factory = sqlite3.Row
        
    def _enable_foreign_keys(self) -> None:
        """Включение поддержки внешних ключей."""
        if self._connection:
            cursor = self._connection.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.close()
    
    def _create_tables(self) -> None:
        """Создание таблиц базы данных."""
        if not self._connection:
            return
            
        cursor = self._connection.cursor()
        
        try:
            # Таблица организаций
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    inn TEXT,
                    ogrn TEXT,
                    address TEXT,
                    phone TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица персон
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS persons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    position TEXT,
                    organization_id INTEGER,
                    order_number TEXT,
                    order_date DATE,
                    nrs_number TEXT,
                    phone TEXT,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (organization_id) REFERENCES organizations(id)
                )
            """)
            
            # Таблица проектов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    contract_number TEXT,
                    contract_date DATE,
                    customer_id INTEGER,
                    contractor_id INTEGER,
                    designer_id INTEGER,
                    start_date DATE,
                    end_date DATE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES organizations(id),
                    FOREIGN KEY (contractor_id) REFERENCES organizations(id),
                    FOREIGN KEY (designer_id) REFERENCES organizations(id)
                )
            """)
            
            # Таблица представителей
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS representatives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    person_id INTEGER NOT NULL,
                    representative_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
                    UNIQUE(project_id, person_id, representative_type)
                )
            """)
            
            # Таблица элементов ВОР
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    vor_number TEXT,
                    section TEXT,
                    subsection TEXT,
                    work_name TEXT NOT NULL,
                    unit TEXT,
                    planned_quantity REAL DEFAULT 0,
                    actual_quantity REAL DEFAULT 0,
                    remaining_quantity REAL DEFAULT 0,
                    location TEXT,
                    floor TEXT,
                    axis TEXT,
                    elevation TEXT,
                    material TEXT,
                    hidden_work BOOLEAN DEFAULT FALSE,
                    work_type TEXT,
                    predecessor_work_id INTEGER,
                    successor_work_id INTEGER,
                    project_document TEXT,
                    drawing_number TEXT,
                    normative_documents TEXT,
                    notes TEXT,
                    status TEXT DEFAULT 'planned',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (predecessor_work_id) REFERENCES work_items(id),
                    FOREIGN KEY (successor_work_id) REFERENCES work_items(id)
                )
            """)
            
            # Таблица документов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    work_item_id INTEGER,
                    document_type TEXT NOT NULL,
                    document_number TEXT,
                    document_date DATE,
                    file_path TEXT,
                    status TEXT DEFAULT 'draft',
                    generated_by_ai BOOLEAN DEFAULT FALSE,
                    manually_edited BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (work_item_id) REFERENCES work_items(id) ON DELETE SET NULL
                )
            """)
            
            # Таблица материалов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    work_item_id INTEGER,
                    name TEXT NOT NULL,
                    manufacturer TEXT,
                    quantity REAL DEFAULT 0,
                    unit TEXT,
                    certificate_number TEXT,
                    certificate_date DATE,
                    passport_number TEXT,
                    passport_date DATE,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (work_item_id) REFERENCES work_items(id) ON DELETE SET NULL
                )
            """)
            
            # Таблица схем
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schemas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    work_item_id INTEGER,
                    schema_number TEXT,
                    name TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (work_item_id) REFERENCES work_items(id) ON DELETE SET NULL
                )
            """)
            
            # Таблица фотографий
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    work_item_id INTEGER,
                    date DATE,
                    description TEXT,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (work_item_id) REFERENCES work_items(id) ON DELETE SET NULL
                )
            """)
            
            # Таблица нормативных документов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS normative_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    revision TEXT,
                    date DATE,
                    application_area TEXT,
                    section TEXT,
                    clause TEXT,
                    text_content TEXT,
                    source TEXT,
                    file_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Таблица шаблонов документов
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    template_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    version TEXT,
                    is_default BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            self._connection.commit()
            
        except sqlite3.Error as e:
            print(f"Ошибка при создании таблиц: {e}")
            raise
        finally:
            cursor.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """Получить подключение к базе данных."""
        if self._connection is None:
            self._connect()
        return self._connection
    
    def execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Выполнить SQL запрос."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor
    
    def commit(self) -> None:
        """Зафиксировать транзакцию."""
        if self._connection:
            self._connection.commit()
    
    def close(self) -> None:
        """Закрыть подключение к базе данных."""
        if self._connection:
            self._connection.close()
            self._connection = None
