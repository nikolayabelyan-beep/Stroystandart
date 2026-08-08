# AI_OFFICE_PROTOCOLS.md - Протоколы работы ИИ-офиса

## P-008: Протокол оценки юридических рисков (Risk Assessment Protocol)

### Цель
Автоматическая оценка юридических рисков документов по шкале 1-10 с генерацией Risk Card.

### Участники
- **Инициатор:** Legal Shredder AI
- **Исполнитель:** Risk Scoring Engine
- **Получатели:** Director, Compliance Checker (при необходимости)

### Алгоритм

#### Шаг 1: Получение документа
```
TRIGGER: Новый документ поступил на обработку
ACTION: Legal Shredder AI извлекает метаданные документа
DATA: document_id, contract_value, deadline_days, sro_permit, и т.д.
```

#### Шаг 2: Оценка по критериям
```
FOR EACH criterion IN criteria_weights:
    - contractual_obligations (вес: 0.25)
    - regulatory_compliance (вес: 0.30)
    - financial_exposure (вес: 0.20)
    - timeline_violations (вес: 0.15)
    - precedent_similarity (вес: 0.10)
    
    CALL: _score_<criterion>(document_data)
    RETURN: score 1-10
```

#### Шаг 3: Расчет итогового scores
```
total_score = SUM(score_i * weight_i) для всех критериев
risk_level = 
    - LOW если total_score <= 3
    - MEDIUM если 4 <= total_score <= 7
    - HIGH если total_score >= 8
```

#### Шаг 4: Выявление критических проблем
```
IF regulatory_compliance >= 7:
    ADD "КРИТИЧНО: Нарушение нормативных требований"
IF financial_exposure >= 7:
    ADD "КРИТИЧНО: Высокие финансовые риски"
IF contractual_obligations >= 8:
    ADD "КРИТИЧНО: Серьезные проблемы с договорными обязательствами"
IF NOT sro_permit:
    ADD "КРИТИЧНО: Отсутствие допуска СРО"
IF counterparty_bankruptcy_risk:
    ADD "ВНИМАНИЕ: Риск банкротства контрагента"
```

#### Шаг 5: Генерация рекомендаций
```
SWITCH risk_level:
    CASE HIGH:
        - "Немедленная эскалация директору"
        - "Требуется внешняя юридическая экспертиза"
        - "Приостановить подписание документа"
    CASE MEDIUM:
        - "Консультация с Compliance Checker"
        - "Запрос дополнительных документов"
        - "Пересмотр спорных условий"
    CASE LOW:
        - "Стандартная процедура обработки"
        - "Мониторинг исполнения"
```

#### Шаг 6: Поиск прецедентов
```
CALL: _find_precedents(document_data)
SEARCH: База прецедентов по ключевым словам
RETURN: Топ-3 релевантных прецедента
```

#### Шаг 7: Генерация Risk Card
```
CREATE RiskCard:
    - risk_id: RISK-YYYYMMDDHHMMSS
    - document_id: из входных данных
    - risk_score: total_score
    - risk_level: LOW|MEDIUM|HIGH
    - assessment_date: текущая дата
    - criteria_scores: все оценки по критериям
    - critical_issues: список проблем
    - recommendations: список рекомендаций
    - escalation_required: true если MEDIUM или HIGH
    - assigned_agent: LEGAL_SHREDDER_AI
    - precedent_matches: найденные прецеденты
```

#### Шаг 8: Эскалация (при необходимости)
```
IF escalation_required == true:
    IF risk_level == HIGH:
        NOTIFY: Director (немедленно)
        ACTION: Приостановить обработку до решения директора
    ELSE IF risk_level == MEDIUM:
        NOTIFY: Compliance Checker
        ACTION: Запросить дополнительную проверку
ELSE:
    CONTINUE: Стандартная обработка
```

### Выходные данные
- Risk Card в формате JSON
- Уведомления в Telegram (для HIGH/MEDIUM)
- Запись в лог аудита

### Метрики эффективности
- Время обработки одного документа: < 30 секунд
- Точность оценки: > 90% (по обратной связи)
- Полнота выявления критических проблем: 100%

---

## P-009: Протокол поиска и применения прецедентов (Precedent Search Protocol)

### Цель
Автоматический поиск релевантных юридических прецедентов и их применение к текущим делам.

### Участники
- **Инициатор:** Legal Shredder AI
- **Исполнитель:** Precedent Engine
- **Пользователи:** Legal Shredder AI, Director

### Алгоритм

#### Шаг 1: Извлечение ключевых параметров
```
INPUT: document_data или case_description
EXTRACT:
    - keywords: ключевые слова (строительство, неустойка, сроки, и т.д.)
    - contract_type: тип договора
    - dispute_subject: предмет спора
    - industry: отрасль
    - region: регион
```

#### Шаг 2: Формирование поискового запроса
```
query = {
    "tags": keywords,
    "contract_type": contract_type,
    "industry": industry,
    "region": region,
    "min_relevance_score": 7
}
```

#### Шаг 3: Поиск в базе прецедентов
```
SEARCH: /workspace/obsidian_vault/03_Legal_Precedents/*.md
FILTER: по параметрам query
RANK: по relevance_score и дате решения
RETURN: Топ-N прецедентов (N=5 по умолчанию)
```

#### Шаг 4: Анализ применимости
```
FOR EACH precedent IN results:
    EVALUATE:
        - similarity_score: схожесть фактов (0-100%)
        - legal_basis_match: совпадение правовых оснований
        - outcome_relevance: применимость исхода дела
        - recency_weight: вес по давности (новые имеют больший вес)
    
    CALCULATE: final_relevance = 
        similarity_score * 0.4 +
        legal_basis_match * 0.3 +
        outcome_relevance * 0.2 +
        recency_weight * 0.1
```

#### Шаг 5: Извлечение уроков (Lessons Learned)
```
FOR EACH top_precedent (relevance > 7):
    EXTRACT:
        - key_findings: ключевые выводы суда
        - risk_factors: факторы риска
        - lessons_learned: извлеченные уроки
        - applicable_scenarios: сценарии применимости
    
    FORMAT: для включения в Risk Card или меморандум
```

#### Шаг 6: Генерация отчета о прецедентах
```
CREATE PrecedentReport:
    - search_date: текущая дата
    - query_parameters: параметры поиска
    - total_found: количество найденных прецедентов
    - top_precedents: список топ-3 с кратким описанием
    - applicability_summary: общая применимость
    - recommended_actions: рекомендованные действия на основе прецедентов
```

#### Шаг 7: Интеграция с Risk Card
```
IF called_from_risk_assessment:
    ADD precedent_matches TO RiskCard
    ADD lessons_learned TO recommendations
    UPDATE risk_score IF negative_precedents_found
```

#### Шаг 8: Обновление базы прецедентов (периодическое)
```
SCHEDULE: Еженедельно (понедельник 09:00)
ACTION:
    - Проверка новых судебных решений
    - Добавление новых прецедентов в базу
    - Актуализация status существующих прецедентов
    - Пересчет relevance_score при изменении законодательства
```

### Выходные данные
- PrecedentReport в формате Markdown
- Список релевантных прецедентов с оценками применимости
- Рекомендации на основе прецедентов

### Метрики эффективности
- Время поиска: < 10 секунд
- Точность подбора: > 85% (по обратной связи юристов)
- Покрытие ключевых сценариев: 100%

---

## Матрица эскалации

| Уровень риска | Кто уведомляется | Время реакции | Действие |
|--------------|------------------|---------------|----------|
| LOW (1-3) | Legal Shredder AI | 24 часа | Стандартная обработка |
| MEDIUM (4-7) | Compliance Checker + Legal Shredder | 4 часа | Дополнительная проверка |
| HIGH (8-10) | Director + Compliance + Legal | Немедленно | Приостановка, внешняя экспертиза |

---

## Аварийные сценарии

### Сценарий A: Недоступность Risk Scoring Engine
```
DETECT: Timeout > 60 секунд при вызове engine
ACTION:
    1. Переключиться на резервный алгоритм (rule-based)
    2. Уведомить Director о деградации функциональности
    3. Логировать все пропущенные оценки для последующей обработки
```

### Сценарий B: Конфликт оценок между агентами
```
DETECT: Разница в оценках风险 > 3 баллов между Legal Shredder и Compliance
ACTION:
    1. Автоматическая эскалация Director
    2. Запрос внешней юридической экспертизы
    3. Приостановка обработки до разрешения конфликта
```

### Сценарий C: Обнаружение критического прецедента
```
DETECT: Найден прецедент с relevance_score > 9 и негативным исходом
ACTION:
    1. Немедленное уведомление Director
    2. Блокировка подписания аналогичных договоров
    3. Экстренный пересмотр всех активных дел на схожесть
```

---

**Версия протокола:** 1.0  
**Дата утверждения:** 2024-01-15  
**Утвердил:** Director AI  
**Ответственный за обновление:** Legal Shredder AI  
**Следующий пересмотр:** 2024-07-15
