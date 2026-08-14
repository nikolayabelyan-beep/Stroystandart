"""
Генератор юридических документов (DOCX)
Интегрируется с Legal Shredder AI для создания официальных писем
"""

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from datetime import datetime
import os

class DocumentGenerator:
    """Генерация .docx документов на основе вердикта юриста"""
    
    def __init__(self, output_dir="generated_docs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def create_fas_addendum(self, complaint_text: str, risk_analysis: dict, precedents: list) -> str:
        """Создание дополнения к жалобе в ФАС"""
        
        doc = Document()
        
        # Заголовок
        header = doc.add_heading('ДОПОЛНЕНИЕ К ЖАЛОБЕ', 0)
        header.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        doc.add_paragraph(f"В Управление Федеральной антимонопольной службы\nпо Ростовской области")
        doc.add_paragraph(f"От: ООО «СТРОЙСТАНДАРТ»\nИНН: 6100000000")
        doc.add_paragraph(f"По делу о нарушении законодательства о закупках")
        doc.add_paragraph("_" * 50)
        
        # Основной текст
        doc.add_heading('Описание ситуации', level=1)
        doc.add_paragraph(complaint_text[:500] + "...")  # Краткое изложение
        
        doc.add_heading('Правовая позиция', level=1)
        doc.add_paragraph(
            "На основании проведенного анализа выявлены следующие нарушения:\n"
            f"- Уровень риска: {risk_analysis.get('level', 'MEDIUM')}\n"
            f"- Оценка соответствия ФЗ-44: {risk_analysis.get('regulatory_score', 7)}/10\n"
            f"- Финансовые риски: {risk_analysis.get('financial_score', 5)}/10"
        )
        
        # Прецеденты
        if precedents:
            doc.add_heading('Судебная практика', level=1)
            for prec in precedents[:2]:
                doc.add_paragraph(f"• {prec.get('id', 'N/A')}: {prec.get('summary', 'N/A')}")
        
        # Требования
        doc.add_heading('Требования', level=1)
        doc.add_paragraph(
            "На основании изложенного, просим:\n"
            "1. Признать действия Заказчика нарушающими ФЗ-44 и ФЗ-135\n"
            "2. Выдать предписание об устранении нарушений\n"
            "3. Признать аукцион несостоявшимся в части спорных требований"
        )
        
        # Приложение
        doc.add_paragraph("\nПриложения:\n1. Расчет несоразмерности требований\n2. Выписки из реестра контрактов\n3. Копии прецедентов")
        
        filename = f"{self.output_dir}/fas_addendum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        doc.save(filename)
        return filename
    
    def create_client_letter(self, client_name: str, contract_num: str, 
                            old_material: str, new_material: str, 
                            characteristics: dict) -> str:
        """Создание письма клиенту о замене материала"""
        
        doc = Document()
        
        # Шапка
        doc.add_paragraph(f"Генеральному директору {client_name}")
        doc.add_paragraph("Исх. № _______ от «___» ________ 2024 г.")
        doc.add_paragraph("_" * 50)
        
        # Заголовок
        title = doc.add_heading('О согласовании замены материала', level=1)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Текст
        doc.add_paragraph(f"Уважаемый руководитель!\n\n"
                         f"В рамках исполнения Государственного контракта № {contract_num}, "
                         f"сообщаем следующее.\n\n"
                         f"Завод-производитель прекратил выпуск утеплителя марки «{old_material}». "
                         f"Предлагаем замену на аналог: «{new_material}».\n\n"
                         f"Обоснование равнозначности:")
        
        # Таблица характеристик
        table = doc.add_table(rows=1, cols=4)
        table.style = 'Table Grid'
        hdr_cells = table.rows[0].cells
        headers = ['Характеристика', 'Проектная марка', 'Предлагаемая марка', 'Примечание']
        for i, text in enumerate(headers):
            hdr_cells[i].text = text
            hdr_cells[i].paragraphs[0].runs[0].bold = True
        
        # Данные (пример)
        data = [
            ('Группа горючести', 'НГ', 'НГ', 'Соответствует ФЗ-123'),
            ('Теплопроводность, Вт/(м·°С)', '≤0.038', '0.036', 'Эффективнее'),
            ('Прочность на сжатие, кПа', '≥10', '12', 'Надежнее'),
        ]
        
        for row_data in data:
            row_cells = table.add_row().cells
            for i, text in enumerate(row_data):
                row_cells[i].text = text
        
        doc.add_paragraph("\nЗамена не влечет ухудшения характеристик или роста стоимости.")
        doc.add_paragraph("Просим согласовать замену в срок до [Дата].")
        
        doc.add_paragraph("\nПриложения:\n1. Письмо завода\n2. Сертификаты\n3. Сравнительная таблица")
        
        doc.add_paragraph("\nС уважением,\nДиректор ООО «СТРОЙСТАНДАРТ»")
        
        filename = f"{self.output_dir}/letter_{client_name.split()[-1]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        doc.save(filename)
        return filename
    
    def create_risk_report(self, document_type: str, risk_score: int, 
                          analysis_details: dict) -> str:
        """Создание отчета об оценке рисков"""
        
        doc = Document()
        
        doc.add_heading('ОТЧЕТ ОБ ОЦЕНКЕ ЮРИДИЧЕСКИХ РИСКОВ', 0)
        doc.add_paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        doc.add_paragraph(f"Тип документа: {document_type}")
        doc.add_paragraph("_" * 50)
        
        # Скор
        score_color = "🟢 НИЗКИЙ" if risk_score <= 3 else ("🟡 СРЕДНИЙ" if risk_score <= 6 else "🔴 ВЫСОКИЙ")
        doc.add_heading(f'Уровень риска: {risk_score}/10 ({score_color})', level=1)
        
        # Детали
        doc.add_heading('Детальный анализ', level=1)
        for key, value in analysis_details.items():
            doc.add_paragraph(f"• {key.replace('_', ' ').title()}: {value}")
        
        # Рекомендации
        doc.add_heading('Рекомендации Legal Shredder AI', level=1)
        if risk_score >= 7:
            doc.add_paragraph("⚠️ ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ РЕШЕНИЕ РУКОВОДИТЕЛЯ")
            doc.add_paragraph("Рекомендуется: Отклонить документ / Потребовать существенных правок")
        elif risk_score >= 4:
            doc.add_paragraph("⚠️ Требуется доработка и согласование с Compliance")
        else:
            doc.add_paragraph("✅ Документ соответствует требованиям, рекомендуется подписание")
        
        filename = f"{self.output_dir}/risk_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        doc.save(filename)
        return filename

# Singleton instance
generator = DocumentGenerator()

def generate_document(content: str, filename: str) -> str:
    """Универсальная функция генерации документа на основе контента"""
    import re
    
    # Определяем тип документа по ключевым словам
    content_lower = content.lower()
    
    if any(word in content_lower for word in ['фас', 'жалоба', 'антимонопольная', 'закупк']):
        return generator.create_fas_addendum(content, {"level": "MEDIUM"}, [])
    elif any(word in content_lower for word in ['письмо', 'клиент', 'заказчик', 'материал', 'замена']):
        # Извлекаем данные из контекста (упрощенно)
        return generator.create_client_letter(
            client_name="Клиент",
            contract_num="№ б/н",
            old_material="Стандартный",
            new_material="Аналог",
            characteristics={}
        )
    elif any(word in content_lower for word in ['риск', 'отчет', 'анализ']):
        return generator.create_risk_report("Анализ", 5, {"details": content[:200]})
    else:
        # Документ общего назначения
        doc = Document()
        doc.add_heading('ДОКУМЕНТ', 0)
        doc.add_paragraph(content)
        doc.add_paragraph("\n_Сгенерировано ИИ-ассистентом ООО 'СТРОЙСТАНДАРТ'_")
        
        filepath = f"{generator.output_dir}/{filename}"
        if not filepath.endswith('.docx'):
            filepath += '.docx'
        doc.save(filepath)
        return filepath
