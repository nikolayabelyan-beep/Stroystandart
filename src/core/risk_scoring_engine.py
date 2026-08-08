"""
Risk Scoring Engine for Legal Shredder AI
Оценка юридических рисков по шкале 1-10 с генерацией Risk Card
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class RiskLevel(Enum):
    LOW = "LOW"       # 1-3
    MEDIUM = "MEDIUM" # 4-7
    HIGH = "HIGH"     # 8-10


@dataclass
class RiskCard:
    """Карточка риска для передачи в систему уведомлений"""
    risk_id: str
    document_id: str
    risk_score: int
    risk_level: str
    assessment_date: str
    criteria_scores: Dict[str, int]
    critical_issues: List[str]
    recommendations: List[str]
    escalation_required: bool
    assigned_agent: str
    precedent_matches: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class RiskScoringEngine:
    """
    Движок оценки юридических рисков
    Интегрируется с Legal Shredder AI
    """
    
    def __init__(self):
        self.criteria_weights = {
            'contractual_obligations': 0.25,      # Нарушение договорных обязательств
            'regulatory_compliance': 0.30,        # Несоблюдение нормативных требований
            'financial_exposure': 0.20,           # Финансовые риски
            'timeline_violations': 0.15,          # Нарушение сроков
            'precedent_similarity': 0.10          # Similarity к негативным прецедентам
        }
        
        self.escalation_thresholds = {
            'low_max': 3,
            'medium_max': 7,
            'high_min': 8
        }
        
    def assess_risk(self, document_data: Dict[str, Any]) -> RiskCard:
        """
        Основная функция оценки риска документа
        
        Args:
            document_data: Данные документа для анализа
            
        Returns:
            RiskCard с полной оценкой
        """
        risk_id = f"RISK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Оценка по каждому критерию (1-10)
        criteria_scores = self._evaluate_criteria(document_data)
        
        # Расчет итогового scores
        total_score = self._calculate_total_score(criteria_scores)
        
        # Определение уровня риска
        risk_level = self._determine_risk_level(total_score)
        
        # Выявление критических проблем
        critical_issues = self._identify_critical_issues(document_data, criteria_scores)
        
        # Генерация рекомендаций
        recommendations = self._generate_recommendations(risk_level, critical_issues)
        
        # Проверка необходимости эскалации
        escalation_required = risk_level in [RiskLevel.MEDIUM, RiskLevel.HIGH]
        
        # Поиск релевантных прецедентов
        precedent_matches = self._find_precedents(document_data)
        
        risk_card = RiskCard(
            risk_id=risk_id,
            document_id=document_data.get('document_id', 'UNKNOWN'),
            risk_score=total_score,
            risk_level=risk_level.value,
            assessment_date=datetime.now().isoformat(),
            criteria_scores=criteria_scores,
            critical_issues=critical_issues,
            recommendations=recommendations,
            escalation_required=escalation_required,
            assigned_agent='LEGAL_SHREDDER_AI',
            precedent_matches=precedent_matches
        )
        
        return risk_card
    
    def _evaluate_criteria(self, document_data: Dict) -> Dict[str, int]:
        """Оценка документа по каждому критерию"""
        scores = {}
        
        # contractual_obligations (1-10)
        scores['contractual_obligations'] = self._score_contractual_risks(document_data)
        
        # regulatory_compliance (1-10)
        scores['regulatory_compliance'] = self._score_regulatory_compliance(document_data)
        
        # financial_exposure (1-10)
        scores['financial_exposure'] = self._score_financial_risks(document_data)
        
        # timeline_violations (1-10)
        scores['timeline_violations'] = self._score_timeline_risks(document_data)
        
        # precedent_similarity (1-10)
        scores['precedent_similarity'] = self._score_precedent_similarity(document_data)
        
        return scores
    
    def _score_contractual_risks(self, data: Dict) -> int:
        """Оценка рисков договорных обязательств"""
        score = 1
        
        # Проверка на отсутствие ключевых разделов
        required_sections = ['subject', 'obligations', 'liability', 'termination']
        missing_sections = sum(1 for section in required_sections if section not in data)
        score += min(missing_sections * 2, 6)
        
        # Проверка на неясные формулировки
        if data.get('vague_terms_count', 0) > 5:
            score += 2
        elif data.get('vague_terms_count', 0) > 2:
            score += 1
            
        # Проверка штрафных санкций
        if data.get('penalty_clauses', {}).get('excessive', False):
            score += 2
            
        return min(score, 10)
    
    def _score_regulatory_compliance(self, data: Dict) -> int:
        """Оценка соответствия нормативным требованиям"""
        score = 1
        
        # Проверка лицензий и допусков СРО
        if not data.get('sro_permit', False):
            score += 4
        elif data.get('sro_permit_expired', False):
            score += 3
            
        # Проверка соответствия строительным нормам
        if data.get('building_code_violations', 0) > 3:
            score += 3
        elif data.get('building_code_violations', 0) > 0:
            score += 1
            
        # Проверка экологических требований
        if data.get('environmental_violations', False):
            score += 2
            
        return min(score, 10)
    
    def _score_financial_risks(self, data: Dict) -> int:
        """Оценка финансовых рисков"""
        score = 1
        
        contract_value = data.get('contract_value', 0)
        advance_payment = data.get('advance_payment_percent', 0)
        
        # Высокая сумма контракта
        if contract_value > 100_000_000:  # 100 млн руб
            score += 2
        elif contract_value > 50_000_000:
            score += 1
            
        # Большой аванс
        if advance_payment > 50:
            score += 3
        elif advance_payment > 30:
            score += 2
        elif advance_payment > 10:
            score += 1
            
        # Проблемы с платежеспособностью контрагента
        if data.get('counterparty_bankruptcy_risk', False):
            score += 3
            
        return min(score, 10)
    
    def _score_timeline_risks(self, data: Dict) -> int:
        """Оценка рисков нарушения сроков"""
        score = 1
        
        deadline_days = data.get('deadline_days', 365)
        
        # Сжатые сроки
        if deadline_days < 30:
            score += 4
        elif deadline_days < 60:
            score += 3
        elif deadline_days < 90:
            score += 2
            
        # История нарушений сроков
        if data.get('past_timeline_violations', 0) > 3:
            score += 3
        elif data.get('past_timeline_violations', 0) > 0:
            score += 1
            
        # Сезонные факторы
        if data.get('seasonal_risk', False):
            score += 2
            
        return min(score, 10)
    
    def _score_precedent_similarity(self, data: Dict) -> int:
        """Оценка схожести с негативными прецедентами"""
        score = 1
        
        # Количество найденных похожих прецедентов
        similar_precedents = data.get('similar_precedents_count', 0)
        
        if similar_precedents > 5:
            score += 4
        elif similar_precedents > 2:
            score += 2
        elif similar_precedents > 0:
            score += 1
            
        # Наличие проигранных дел по схожим вопросам
        if data.get('lost_cases_similar', False):
            score += 3
            
        return min(score, 10)
    
    def _calculate_total_score(self, criteria_scores: Dict[str, int]) -> int:
        """Расчет итогового scores риска"""
        total = 0
        for criterion, score in criteria_scores.items():
            weight = self.criteria_weights.get(criterion, 0.1)
            total += score * weight
            
        return round(total)
    
    def _determine_risk_level(self, score: int) -> RiskLevel:
        """Определение уровня риска"""
        if score <= self.escalation_thresholds['low_max']:
            return RiskLevel.LOW
        elif score <= self.escalation_thresholds['medium_max']:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def _identify_critical_issues(self, data: Dict, scores: Dict) -> List[str]:
        """Выявление критических проблем"""
        issues = []
        
        if scores.get('regulatory_compliance', 0) >= 7:
            issues.append("КРИТИЧНО: Нарушение нормативных требований")
            
        if scores.get('financial_exposure', 0) >= 7:
            issues.append("КРИТИЧНО: Высокие финансовые риски")
            
        if scores.get('contractual_obligations', 0) >= 8:
            issues.append("КРИТИЧНО: Серьезные проблемы с договорными обязательствами")
            
        if not data.get('sro_permit', False):
            issues.append("КРИТИЧНО: Отсутствие допуска СРО")
            
        if data.get('counterparty_bankruptcy_risk', False):
            issues.append("ВНИМАНИЕ: Риск банкротства контрагента")
            
        return issues
    
    def _generate_recommendations(self, level: RiskLevel, issues: List[str]) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []
        
        if level == RiskLevel.HIGH:
            recommendations.append("Немедленная эскалация директору")
            recommendations.append("Требуется внешняя юридическая экспертиза")
            recommendations.append("Приостановить подписание документа")
        elif level == RiskLevel.MEDIUM:
            recommendations.append("Консультация с Compliance Checker")
            recommendations.append("Запрос дополнительных документов")
            recommendations.append("Пересмотр спорных условий")
        else:
            recommendations.append("Стандартная процедура обработки")
            recommendations.append("Мониторинг исполнения")
            
        return recommendations
    
    def _find_precedents(self, data: Dict) -> List[str]:
        """Поиск релевантных прецедентов (заглушка для интеграции)"""
        # В реальной системе здесь будет поиск по базе прецедентов
        keywords = data.get('keywords', [])
        precedents = []
        
        if 'construction' in str(keywords).lower():
            precedents.append("PREC-2023-001: Нарушение сроков строительства")
            precedents.append("PREC-2023-015: Споры по качеству работ")
            
        if 'payment' in str(keywords).lower():
            precedents.append("PREC-2022-042: Невыполнение платежных обязательств")
            
        return precedents[:3]  # Возвращаем топ-3
    
    def export_risk_card(self, risk_card: RiskCard, filepath: str):
        """Экспорт Risk Card в JSON"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(risk_card.to_dict(), f, indent=2, ensure_ascii=False)


# Пример использования
if __name__ == "__main__":
    engine = RiskScoringEngine()
    
    # Тестовые данные документа
    test_document = {
        'document_id': 'DOC-2024-001',
        'contract_value': 75_000_000,
        'advance_payment_percent': 40,
        'deadline_days': 45,
        'sro_permit': True,
        'sro_permit_expired': False,
        'building_code_violations': 1,
        'past_timeline_violations': 2,
        'counterparty_bankruptcy_risk': False,
        'vague_terms_count': 3,
        'similar_precedents_count': 2,
        'keywords': ['construction', 'payment']
    }
    
    risk_card = engine.assess_risk(test_document)
    print(f"Risk Score: {risk_card.risk_score}/10")
    print(f"Risk Level: {risk_card.risk_level}")
    print(f"Escalation Required: {risk_card.escalation_required}")
    print(f"Critical Issues: {risk_card.critical_issues}")
    
    # Экспорт в файл
    engine.export_risk_card(risk_card, '/workspace/templates/sample_risk_card.json')
    print("\nRisk Card exported to /workspace/templates/sample_risk_card.json")
