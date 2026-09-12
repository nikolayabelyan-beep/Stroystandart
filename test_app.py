#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки работы приложения.
Запустите: python test_app.py
"""

import sys
from pathlib import Path

# Добавляем корень приложения в путь
sys.path.insert(0, str(Path(__file__).parent))

from app.database.db_manager import DatabaseManager
from app.database.repositories import (
    OrganizationRepository, PersonRepository, ProjectRepository,
    RepresentativeRepository, WorkItemRepository
)
from app.database.models.models import (
    Organization, Person, Project, Representative, WorkItem
)


def test_database():
    """Тестирование базы данных."""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    # Инициализация БД
    db = DatabaseManager.get_instance()
    db.initialize()
    print(f"✅ База данных инициализирована")
    print(f"📁 Путь к БД: {db.db_path}")
    
    # Проверка таблиц
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"✅ Таблицы созданы: {len(tables)} шт.")
    for t in tables:
        if not t.startswith('sqlite_'):
            print(f"   - {t}")
    
    return True


def test_crud_operations():
    """Тестирование CRUD операций."""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ CRUD ОПЕРАЦИЙ")
    print("=" * 60)
    
    db = DatabaseManager.get_instance()
    
    # Тест организаций
    print("\n📋 Тест организаций...")
    org = Organization(
        name='ООО СтройМонтаж',
        inn='7701234567',
        ogrn='1027700000000',
        address='г. Москва, ул. Строителей, 1',
        phone='+7 (495) 123-45-67',
        email='info@stroymontazh.ru'
    )
    org_id = OrganizationRepository.create(org)
    print(f"✅ Организация создана: ID={org_id}")
    
    org_loaded = OrganizationRepository.get_by_id(org_id)
    assert org_loaded is not None
    assert org_loaded.name == 'ООО СтройМонтаж'
    print(f"✅ Организация загружена: {org_loaded.name}")
    
    # Тест персоны
    print("\n👤 Тест персон...")
    person = Person(
        full_name='Иванов Иван Иванович',
        position='Главный инженер',
        organization_id=org_id,
        order_number='123-к',
        order_date=Path('2024-01-15').__class__('2024-01-15') if False else type('obj', (object,), {'isoformat': lambda self: '2024-01-15'})(),
        nrs_number='НР-001',
        phone='+7 (900) 123-45-67',
        email='ivanov@stroymontazh.ru'
    )
    from datetime import date
    person.order_date = date(2024, 1, 15)
    
    person_id = PersonRepository.create(person)
    print(f"✅ Персона создана: ID={person_id}")
    
    person_loaded = PersonRepository.get_by_id(person_id)
    assert person_loaded is not None
    assert person_loaded.full_name == 'Иванов Иван Иванович'
    print(f"✅ Персона загружена: {person_loaded.full_name}")
    
    # Тест проекта
    print("\n🏗️ Тест проектов...")
    from datetime import date
    project = Project(
        name='Тестовый объект - Строительство склада',
        address='г. Москва, ул. Примерная, 10',
        contract_number='Д-001/2024',
        contract_date=date(2024, 1, 1),
        customer_id=org_id,
        contractor_id=org_id,
        designer_id=None,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 12, 31),
        description='Тестовый проект для проверки функциональности'
    )
    
    project_id = ProjectRepository.create(project)
    print(f"✅ Проект создан: ID={project_id}")
    
    project_loaded = ProjectRepository.get_by_id(project_id)
    assert project_loaded is not None
    assert project_loaded.name == 'Тестовый объект - Строительство склада'
    print(f"✅ Проект загружен: {project_loaded.name}")
    print(f"   Адрес: {project_loaded.address}")
    print(f"   Договор: {project_loaded.contract_number} от {project_loaded.contract_date}")
    
    # Тест представителя
    print("\n👔 Тест представителей...")
    rep = Representative(
        project_id=project_id,
        person_id=person_id,
        representative_type='подрядчик'
    )
    
    rep_id = RepresentativeRepository.create(rep)
    print(f"✅ Представитель назначен: ID={rep_id}")
    
    reps = RepresentativeRepository.get_by_project(project_id)
    assert len(reps) > 0
    print(f"✅ Представители проекта: {len(reps)} чел.")
    
    # Тест ВОР
    print("\n📊 Тест ВОР...")
    work_items = [
        WorkItem(
            project_id=project_id,
            vor_number='1',
            work_name='Устройство фундамента',
            unit='м3',
            planned_quantity=100.0,
            location='Ось 1-5',
            hidden_work=True,
            work_type='Земляные работы'
        ),
        WorkItem(
            project_id=project_id,
            vor_number='2',
            work_name='Монтаж стен',
            unit='м2',
            planned_quantity=250.0,
            location='1 этаж',
            hidden_work=False,
            work_type='Монтажные работы'
        ),
        WorkItem(
            project_id=project_id,
            vor_number='3',
            work_name='Устройство кровли',
            unit='м2',
            planned_quantity=125.0,
            location='Покрытие',
            hidden_work=False,
            work_type='Кровельные работы'
        )
    ]
    
    count = WorkItemRepository.bulk_insert(work_items)
    print(f"✅ Элементы ВОР добавлены: {count} шт.")
    
    works = WorkItemRepository.get_by_project(project_id)
    print(f"✅ Работы в проекте: {len(works)} шт.")
    for w in works:
        remaining = w.planned_quantity - w.actual_quantity
        status_color = "🟢" if remaining >= 0 else "🔴"
        print(f"   {status_color} {w.vor_number}. {w.work_name}: {w.planned_quantity} {w.unit} (остаток: {remaining})")
    
    # Тест обновления фактического объёма
    print("\n✏️ Тест обновления объёмов...")
    if works:
        work = works[0]
        work.actual_quantity = 50.0
        work.update_quantities()
        WorkItemRepository.update(work)
        print(f"✅ Фактический объём обновлён: {work.actual_quantity} из {work.planned_quantity} {work.unit}")
        print(f"   Остаток: {work.remaining_quantity} {work.unit}")
    
    return True


def test_ui_imports():
    """Тестирование импорта UI модулей."""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ UI МОДУЛЕЙ")
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        print("✅ PySide6 импортирован")
        
        # Пробуем импортировать основные виджеты
        from app.ui.main_window import MainWindow
        print("✅ MainWindow импортирован")
        
        from app.ui.project_dialog import ProjectDialog
        print("✅ ProjectDialog импортирован")
        
        from app.ui.vor_widget import VorWidget
        print("✅ VorWidget импортирован")
        
        from app.ui.settings_widget import SettingsWidget
        print("✅ SettingsWidget импортирован")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта UI: {e}")
        return False


def main():
    """Основная функция тестирования."""
    print("\n" + "🚀" * 30)
    print("ПРОВЕРКА ПРИЛОЖЕНИЯ 'СТРОЙДОКУМЕНТ'")
    print("🚀" * 30 + "\n")
    
    results = []
    
    # Тест 1: База данных
    try:
        results.append(("База данных", test_database()))
    except Exception as e:
        print(f"❌ Ошибка теста БД: {e}")
        results.append(("База данных", False))
    
    # Тест 2: CRUD операции
    try:
        results.append(("CRUD операции", test_crud_operations()))
    except Exception as e:
        print(f"❌ Ошибка CRUD: {e}")
        import traceback
        traceback.print_exc()
        results.append(("CRUD операции", False))
    
    # Тест 3: UI модули
    try:
        results.append(("UI модули", test_ui_imports()))
    except Exception as e:
        print(f"❌ Ошибка UI: {e}")
        results.append(("UI модули", False))
    
    # Итоговый отчёт
    print("\n" + "=" * 60)
    print("ИТОГОВЫЙ ОТЧЁТ")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")
    
    print(f"\n📊 Пройдено тестов: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("\n📝 Для запуска приложения выполните:")
        print("   python app/main.py")
        print("\n💡 Для установки Ollama (локальный ИИ):")
        print("   1. Скачайте с https://ollama.ai")
        print("   2. Установите модель: ollama pull llama3.1")
        print("   3. В настройках приложения укажите URL: http://127.0.0.1:11434")
    else:
        print("\n⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        sys.exit(1)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
