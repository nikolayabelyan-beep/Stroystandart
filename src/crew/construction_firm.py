from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta

from src.crew.protocol_guard import validate_required_sources

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MASTER_CONTRACTS_PATH = BASE_DIR / "obsidian_vault" / "MASTER_CONTRACTS.md"
MY_COMPANY_PATH = BASE_DIR / "obsidian_vault" / "MY_COMPANY.md"
PROTOCOLS_PATH = BASE_DIR / "obsidian_vault" / "02_Protocols" / "AI_OFFICE_PROTOCOLS.md"
TEMPLATES_INDEX_PATH = BASE_DIR / "obsidian_vault" / "02_Protocols" / "DOCUMENT_TEMPLATES_INDEX.md"
LEGAL_INDEX_PATH = BASE_DIR / "obsidian_vault" / "01_Law" / "LEGAL_REFERENCE_INDEX.md"
LATEST_LEGAL_UPDATE_PATH = BASE_DIR / "obsidian_vault" / "01_Law" / "Updates" / "LATEST_UPDATES.md"
GENERAL_LETTER_TEMPLATE_PATH = BASE_DIR / "data" / "templates" / "general_official_letter.md"
DECISION_MEMO_TEMPLATE_PATH = BASE_DIR / "data" / "templates" / "director_decision_memo.md"
LEGAL_CLAIM_TEMPLATE_PATH = BASE_DIR / "data" / "templates" / "legal_claim_letter.md"
LEGAL_CLARIFICATION_TEMPLATE_PATH = BASE_DIR / "data" / "templates" / "legal_clarification_request.md"
ROLE_MEMORY_DIR = BASE_DIR / "data" / "agents" / "memory"
ROLE_MEMORY_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Contract:
    object_name: str
    customer: str
    contract_info: str
    contract_no: str
    price: float
    deadline: str


@dataclass
class CompanyProfile:
    full_name: str
    director_name: str
    inn: str
    kpp: str
    address: str
    email: str


@dataclass
class ReviewDecision:
    approved: bool
    comments: list[str]


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_money(text: str) -> float:
    cleaned = text.replace("₽", "").replace(" ", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def _parse_contracts() -> list[Contract]:
    content = _read(MASTER_CONTRACTS_PATH)
    pattern = re.compile(r"###\s+\d+\.\s+Объект:\s+(.+?)\n([\s\S]*?)(?=\n---|\n###\s+\d+\.|$)")
    contracts: list[Contract] = []

    for object_name_raw, block in pattern.findall(content):
        def cap(label: str) -> str:
            m = re.search(rf"\*\s*\*\*{label}:\*\*\s*(.+)", block)
            return (m.group(1).strip() if m else "")

        contract_info = cap(r"Контракт")
        contract_no = re.sub(r"^№\s*", "", contract_info)
        contract_no = re.sub(r"\s+от\s+\d{2}\.\d{2}\.\d{4}$", "", contract_no)
        contracts.append(
            Contract(
                object_name=object_name_raw.strip(),
                customer=cap(r"Заказчик \(Полное\)"),
                contract_info=contract_info,
                contract_no=contract_no.strip(),
                price=_parse_money(cap(r"Цена контракта")),
                deadline=cap(r"Срок исполнения"),
            )
        )

    return contracts


def _company_profile() -> CompanyProfile:
    content = _read(MY_COMPANY_PATH)

    def cap(label: str) -> str:
        match = re.search(rf"\*\s*\*\*{label}:\*\*\s*(.+)", content)
        return match.group(1).strip() if match else ""

    return CompanyProfile(
        full_name=cap(r"Полное наименование"),
        director_name=cap(r"Генеральный директор"),
        inn=cap(r"ИНН"),
        kpp=cap(r"КПП"),
        address=cap(r"Юридический адрес"),
        email=cap(r"E-mail"),
    )


def _today() -> str:
    return datetime.now().strftime("%d.%m.%Y")


def _next_days(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")


def _outgoing_number(prefix: str) -> str:
    return f"{prefix}-{datetime.now().strftime('%y%m%d-%H%M')}"


def _render_template(path: Path, values: dict[str, str]) -> str:
    content = _read(path)
    for key, value in values.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return re.sub(r"{{[^{}]+}}", "________________", content)


def _memory_path(role_id: str) -> Path:
    return ROLE_MEMORY_DIR / f"{role_id}.json"


def _load_role_memory(role_id: str) -> list[str]:
    path = _memory_path(role_id)
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload[-10:]]


def _save_role_memory(role_id: str, notes: list[str]) -> None:
    path = _memory_path(role_id)
    existing = _load_role_memory(role_id)
    merged: list[str] = []
    for note in existing + [n for n in notes if n]:
        note = note.strip()
        if note and note not in merged:
            merged.append(note)
    merged = merged[-10:]
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")


def _memory_block(role_id: str) -> str:
    notes = _load_role_memory(role_id)
    if not notes:
        return ""
    lines = ["Учитывай замечания директора из памяти:"]
    for note in notes[-3:]:
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def _contains_unresolved_placeholders(text: str) -> bool:
    normalized = text
    normalized = re.sub(r"Signature:\s*_+", "Signature: OK", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"Подпись:\s*_+", "Подпись: OK", normalized, flags=re.IGNORECASE)
    return "________________" in normalized


def _director_review(executor_role_id: str, draft: str, user_text: str) -> ReviewDecision:
    comments: list[str] = []
    lowered = user_text.lower()

    if _contains_unresolved_placeholders(draft):
        comments.append("Заполни все незаполненные поля и убери пустые placeholders.")
    if executor_role_id == "legal_shredder":
        if "To:" in draft and "Контрагент / Заказчик" in draft:
            comments.append("Уточни конкретного адресата письма.")
        if "Subject:" in draft and "О направлении официального письма" in draft and "письмо" in lowered:
            comments.append("Сделай тему письма более предметной по задаче пользователя.")
        if "исх-______/26".lower() in draft.lower() or "прет-______/26".lower() in draft.lower() or "запр-______/26".lower() in draft.lower():
            comments.append("Подготовь проект исходящего номера или пометь порядок его присвоения.")
    if executor_role_id == "pto_engineer":
        if "Contract amount covered: ________________" in draft or "amount: ________________" in draft.lower():
            comments.append("Укажи сумму или явно перечисли, какие данные нужны от пользователя для выпуска документа.")
        if "Чек-лист заполнения" in draft and "Подписи" in draft:
            comments.append("Добавь перечень обязательных приложений и ответственных за подписание.")
    if executor_role_id == "finance_controller":
        if "Severity: Средняя" in draft and any(token in lowered for token in ["срочно", "критично", "разрыв"]):
            comments.append("Пересмотри severity и увяжи ее с реальным уровнем финансового риска.")
        if "________________" in draft:
            comments.append("Заполни все финансовые поля или перечисли недостающие исходные данные.")

    return ReviewDecision(approved=not comments, comments=comments)


def _extract_addressee(text: str, contracts: list[Contract]) -> str:
    related = _find_related_contracts(text, contracts)
    if related:
        return related[0].customer
    match = re.search(r"(?:для|в адрес|кому)\s+(.+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip(" .,:;")
    return "Контрагент / Заказчик"


def _detect_document_intent(text: str) -> str | None:
    normalized = text.lower()
    if any(token in normalized for token in ["претенз", "досудеб", "нарушен", "задолж", "оплатите"]):
        return "claim_letter"
    if any(token in normalized for token in ["разъяснен", "уточнен", "уточни", "clarification"]):
        return "clarification_request"
    if any(token in normalized for token in ["служеб", "решени", "резолюц", "записк"]):
        return "decision_memo"
    if any(token in normalized for token in ["письмо", "letter", "составь письмо", "напиши письмо"]):
        return "general_letter"
    return None


def _detect_pto_intent(text: str) -> str | None:
    normalized = text.lower()
    if "кс-2" in normalized:
        return "ks2_cover"
    if "кс-3" in normalized:
        return "ks3_cover"
    if "аоср" in normalized or "исполнительн" in normalized:
        return "aosr"
    return None


def _general_letter_reply(user_text: str, contracts: list[Contract]) -> str:
    company = _company_profile()
    related = _find_related_contracts(user_text, contracts)
    contract_number = related[0].contract_no if related else "не указан пользователем"
    object_name = related[0].object_name if related else "объект уточняется"
    addressee = _extract_addressee(user_text, contracts)
    subject = "О направлении официального письма"
    if "оплат" in user_text.lower():
        subject = "О необходимости оплаты по договору"
    elif "соглас" in user_text.lower():
        subject = "О согласовании документов"
    elif "ответ" in user_text.lower():
        subject = "О предоставлении ответа"

    draft = _render_template(
        GENERAL_LETTER_TEMPLATE_PATH,
        {
            "date": _today(),
            "outgoing_number": _outgoing_number("ИСХ"),
            "addressee": addressee,
            "subject": subject,
            "company_full_name": company.full_name,
            "director_name": company.director_name,
            "contract_number": contract_number,
            "object_name": object_name,
            "body": (
                "Сообщаем вам следующую позицию по вопросу, изложенному в обращении.\n"
                "Просим рассмотреть настоящее письмо и сообщить итоговое решение в рабочем порядке.\n"
                "При необходимости готовы оперативно предоставить подтверждающие документы и пояснения."
            ),
            "contact_email": company.email or "указать корпоративный e-mail при выпуске",
        },
    )
    memory = _memory_block("legal_shredder")
    if memory:
        draft = memory + draft
    return "\n".join(
        [
            "Роль: LEGAL_SHREDDER (подготовка письма)",
            "Результат: подготовлен черновик официального письма.",
            draft,
            "Следующий шаг: уточнить адресата, тему и номер исходящего перед отправкой.",
        ]
    )


def _decision_memo_reply(user_text: str) -> str:
    company = _company_profile()
    draft = _render_template(
        DECISION_MEMO_TEMPLATE_PATH,
        {
            "memo_id": f"DM-{datetime.now().strftime('%Y%m%d-%H%M')}",
            "date": _today(),
            "initiator_role": "Исполнительный Директор",
            "decision_topic": user_text.strip() or "Управленческое решение по задаче",
            "option_1": "Исполнить в текущем контуре силами внутренней команды",
            "option_2": "Эскалировать вопрос профильному исполнителю с контролем директора",
            "chosen_option": "Исполнить и поставить на контроль",
            "rationale": "Требуется оперативное решение с фиксацией ответственности и срока.",
            "execution_owner": "Профильный исполнитель / Директор",
            "execution_deadline": _next_days(2),
            "director_name": company.director_name,
        },
    )
    return "\n".join(
        [
            "Роль: DIRECTOR_EXECUTION",
            "Результат: подготовлена управленческая записка / резолюция.",
            draft,
        ]
    )


def _pto_execution_reply(user_text: str, contracts: list[Contract]) -> str:
    company = _company_profile()
    related = _find_related_contracts(user_text, contracts)
    contract = related[0] if related else None
    pto_intent = _detect_pto_intent(user_text)

    if pto_intent == "ks2_cover":
        template = _read(BASE_DIR / "data" / "templates" / "ks2_cover_letter.md")
        rendered = _memory_block("pto_engineer") + template
        replacements = {
            "date": _today(),
            "outgoing_number": _outgoing_number("КС2"),
            "customer_full_name": contract.customer if contract else "уточнить заказчика по договору",
            "contract_number": contract.contract_no if contract else "уточнить номер контракта",
            "period_start": _today(),
            "period_end": _next_days(30),
            "amount": "Сумма определяется по акту КС-2 и расчету подрядчика",
            "responsible_person": "Инженер ПТО",
            "director_name": company.director_name,
        }
        for key, value in replacements.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        return "\n".join(
            [
                "Роль: PTO_ENGINEER (исполнение документа)",
                "Результат: подготовлено сопроводительное письмо к КС-2.",
                rendered,
            ]
        )

    if pto_intent == "ks3_cover":
        template = _read(BASE_DIR / "data" / "templates" / "ks3_cover_letter.md")
        rendered = _memory_block("pto_engineer") + template
        replacements = {
            "date": _today(),
            "outgoing_number": _outgoing_number("КС3"),
            "customer_full_name": contract.customer if contract else "уточнить заказчика по договору",
            "contract_number": contract.contract_no if contract else "уточнить номер контракта",
            "period": f"{_today()} - {_next_days(30)}",
            "amount": "Сумма определяется по справке КС-3 и расчету подрядчика",
            "vat_info": "НДС 5%",
            "responsible_person": "Инженер ПТО",
            "director_name": company.director_name,
        }
        for key, value in replacements.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        return "\n".join(
            [
                "Роль: PTO_ENGINEER (исполнение документа)",
                "Результат: подготовлено сопроводительное письмо к КС-3.",
                rendered,
            ]
        )

    if pto_intent == "aosr":
        lines = [
            "Роль: PTO_ENGINEER (исполнение документа)",
            "Результат: подготовлен каркас АОСР / исполнительного документа.",
            f"Объект: {contract.object_name if contract else 'объект уточняется'}",
            f"Контракт: {contract.contract_no if contract else 'уточнить номер контракта'}",
            "Чек-лист заполнения:",
            "1. Основание производства работ",
            "2. Наименование скрытых работ",
            "3. Период выполнения",
            "4. Исполнительная схема / фотофиксация",
            "5. Материалы и сертификаты",
            "6. Подписи участников освидетельствования",
        ]
        memory = _memory_block("pto_engineer")
        if memory:
            lines.insert(2, memory.strip())
        return "\n".join(lines)

    return _pto_reply(user_text, contracts)


def _claim_letter_reply(user_text: str, contracts: list[Contract]) -> str:
    company = _company_profile()
    related = _find_related_contracts(user_text, contracts)
    contract = related[0] if related else None
    customer = contract.customer if contract else "Контрагент / Заказчик"
    contract_no = contract.contract_no if contract else "уточнить номер договора"
    draft = _render_template(
        LEGAL_CLAIM_TEMPLATE_PATH,
        {
            "date": _today(),
            "outgoing_number": _outgoing_number("ПРЕТ"),
            "customer_full_name": customer,
            "customer_inn_kpp": "уточнить по карточке контрагента",
            "customer_address": "уточнить по договору / ЕГРЮЛ",
            "company_full_name": company.full_name,
            "company_inn_kpp": f"{company.inn} / {company.kpp}",
            "company_address": company.address,
            "contract_number": contract_no,
            "contract_date": _today(),
            "breach_description": "Нарушение обязательств по договору / отсутствие оплаты / отсутствие ответа по документам.",
            "civil_code_reference": "ГК РФ: обязательства должны исполняться надлежащим образом.",
            "procurement_reference": "Условия контракта и подтверждающие документы.",
            "claim_amount": "подлежит уточнению по расчету задолженности",
            "payment_deadline": _next_days(7),
            "attachment_1": "Копия договора",
            "attachment_2": "Подтверждающие документы",
            "director_name": company.director_name,
        },
    )
    memory = _memory_block("legal_shredder")
    if memory:
        draft = memory + draft
    return "\n".join(
        [
            "Роль: LEGAL_SHREDDER (исполнение документа)",
            "Результат: подготовлен черновик претензии.",
            draft,
            "Следующий шаг: заполнить сумму требований и реквизиты адресата.",
        ]
    )


def _clarification_request_reply(user_text: str, contracts: list[Contract]) -> str:
    company = _company_profile()
    related = _find_related_contracts(user_text, contracts)
    contract_no = related[0].contract_no if related else "уточнить номер договора"
    addressee = _extract_addressee(user_text, contracts)
    draft = _render_template(
        LEGAL_CLARIFICATION_TEMPLATE_PATH,
        {
            "date": _today(),
            "outgoing_number": _outgoing_number("ЗАПР"),
            "counterparty_name": addressee,
            "contract_number": contract_no,
            "questions_block": "Просим дать письменные разъяснения по спорным положениям и порядку исполнения обязательств.",
            "response_deadline": _next_days(5),
            "contract_clause_reference": "уточнить конкретный пункт договора при выпуске",
            "legal_reference": "ГК РФ / условия договора / локальные регламенты",
            "director_name": company.director_name,
        },
    )
    memory = _memory_block("legal_shredder")
    if memory:
        draft = memory + draft
    return "\n".join(
        [
            "Роль: LEGAL_SHREDDER (исполнение документа)",
            "Результат: подготовлен запрос о разъяснении.",
            draft,
        ]
    )


def _finance_execution_reply(user_text: str, contracts: list[Contract]) -> str:
    template = _read(BASE_DIR / "data" / "templates" / "escalation_risk_card.md")
    related = _find_related_contracts(user_text, contracts)
    contract = related[0] if related else None
    rendered = _memory_block("finance_controller") + template
    lowered = user_text.lower()
    is_high_risk = any(token in lowered for token in ["срочно", "критично", "разрыв", "кассов"])
    replacements = {
        "risk_id": f"RISK-{datetime.now().strftime('%Y%m%d-%H%M')}",
        "date": _today(),
        "owner_role": "Финансы",
        "contract_number": contract.contract_no if contract else "уточнить номер договора",
        "risk_type": "Финансовый риск / кассовый разрыв",
        "severity": "Высокая" if is_high_risk else "Средняя",
        "risk_description": "Требуется финансовый контроль по обязательствам, оплатам и кассовой нагрузке.",
        "impact": "Возможная просрочка платежей, блокировка работ, эскалация директору.",
        "option_1": "Перенести часть платежей",
        "option_2": "Ускорить выставление / приемку документов",
        "option_3": "Согласовать резервирование денежных средств",
        "decision_deadline": _next_days(2),
    }
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return "\n".join(
        [
            "Роль: FINANCE_CONTROLLER (исполнение документа)",
            "Результат: подготовлена финансовая риск-карта / эскалация.",
            rendered,
        ]
    )


def _role_id(agent_name: str, user_text: str) -> str:
    name = (agent_name or "").lower()
    text = (user_text or "").lower()

    if "исполнительный директор" in name or (("директор" in name) and ("финансов" not in name)):
        return "director"

    if "пто" in name or any(x in text for x in ["аоср", "кс-2", "кс-3", "исполнительн"]):
        return "pto_engineer"
    if "юрист" in name or any(x in text for x in ["претенз", "прав", "суд", "44-фз", "223-фз"]):
        return "legal_shredder"
    if "фин" in name or any(x in text for x in ["оплат", "касс", "ддс", "расход", "прибыл"]):
        return "finance_controller"
    return "director"


def _find_related_contracts(query: str, contracts: list[Contract]) -> list[Contract]:
    q = query.lower()
    out: list[Contract] = []
    for c in contracts:
        hay = f"{c.object_name} {c.customer} {c.contract_no}".lower()
        if c.contract_no and c.contract_no.lower() in q:
            out.append(c)
            continue
        if any(token in hay for token in re.findall(r"[а-яa-z0-9]{4,}", q)):
            out.append(c)
    # unique preserve order
    uniq: list[Contract] = []
    seen: set[str] = set()
    for c in out:
        key = c.contract_no or c.object_name
        if key not in seen:
            seen.add(key)
            uniq.append(c)
    return uniq[:3]


def _director_reply(user_text: str, contracts: list[Contract]) -> str:
    intent = _detect_document_intent(user_text)
    routed_role = _role_id("", user_text)

    def approved_block(executor_name: str, next_step: str) -> str:
        return "\n".join(
            [
                "",
                "Проверка директора:",
                f"- Исполнитель: {executor_name}",
                "- Статус: проверено директором",
                "- Резолюция: передать пользователю как рабочий черновик",
                f"- Следующий шаг: {next_step}",
            ]
        )

    def rework_block(executor_name: str, role_id: str, comments: list[str]) -> str:
        _save_role_memory(role_id, comments)
        lines = [
            f"Результат возвращен на доработку исполнителю: {executor_name}",
            "Замечания директора:",
        ]
        lines.extend(f"- {comment}" for comment in comments)
        lines.append("Замечания сохранены в память сотрудника и будут учитываться в следующих ответах.")
        return "\n".join(lines)

    def review_worker(
        executor_name: str,
        role_id: str,
        next_step: str,
        worker_fn,
    ) -> str:
        worker_result = worker_fn()
        review = _director_review(role_id, worker_result, user_text)
        if review.approved:
            return worker_result + approved_block(executor_name, next_step)

        _save_role_memory(role_id, review.comments)

        improved_result = worker_fn()
        second_review = _director_review(role_id, improved_result, user_text)
        if second_review.approved:
            return improved_result + approved_block(
                executor_name,
                f"{next_step}; замечания директора учтены после доработки",
            )

        return rework_block(executor_name, role_id, second_review.comments)

    if intent == "decision_memo":
        return _decision_memo_reply(user_text) + approved_block("Директор", "утвердить исполнителя и срок")

    if intent in {"general_letter", "claim_letter", "clarification_request"} or routed_role == "legal_shredder":
        if intent == "claim_letter":
            return review_worker(
                "Юрист",
                "legal_shredder",
                "уточнить реквизиты, адресата и исходящий номер",
                lambda: _claim_letter_reply(user_text, contracts),
            )
        if intent == "clarification_request":
            return review_worker(
                "Юрист",
                "legal_shredder",
                "уточнить пункт договора и адресата",
                lambda: _clarification_request_reply(user_text, contracts),
            )
        return review_worker(
            "Юрист",
            "legal_shredder",
            "уточнить реквизиты, адресата и исходящий номер",
            lambda: _general_letter_reply(user_text, contracts),
        )

    if routed_role == "pto_engineer":
        return review_worker(
            "ПТО",
            "pto_engineer",
            "проверить комплектность приложений и подписи",
            lambda: _pto_execution_reply(user_text, contracts),
        )

    if routed_role == "finance_controller":
        return review_worker(
            "Финансы",
            "finance_controller",
            "подтвердить суммы, срок и финансовое решение",
            lambda: _finance_execution_reply(user_text, contracts),
        )

    total = sum(c.price for c in contracts)
    related = _find_related_contracts(user_text, contracts)
    lines = [
        "Роль: DIRECTOR (протоколы P-001, P-006, P-007)",
        f"Контрактов в реестре: {len(contracts)}; суммарно: {total:,.2f} RUB".replace(",", " "),
        "Действие: задача принята и маршрутизирована по протоколу.",
    ]
    if related:
        lines.append("Контекст по задаче:")
        for c in related:
            lines.append(f"- {c.object_name} | {c.contract_no} | дедлайн {c.deadline}")
    lines.append("Следующий шаг: сформировать исполнение через профильную роль (ПТО/Юрист/Финансы).")
    return "\n".join(lines)


def _pto_reply(user_text: str, contracts: list[Contract]) -> str:
    related = _find_related_contracts(user_text, contracts)
    lines = [
        "Роль: PTO_ENGINEER (протоколы P-001, P-002, P-003, P-005)",
        "Готовлю документ только по validated данным из MASTER_CONTRACTS.md и MY_COMPANY.md.",
        f"Шаблоны: {TEMPLATES_INDEX_PATH.relative_to(BASE_DIR)}",
    ]
    if related:
        c = related[0]
        lines.append("Выбран базовый контракт для подготовки черновика:")
        lines.append(f"- Объект: {c.object_name}")
        lines.append(f"- Контракт: {c.contract_no}")
        lines.append(f"- Заказчик: {c.customer}")
        lines.append("Чек-лист полей: номер акта, период, виды работ, материалы, подтверждающие документы, подписи.")
    else:
        lines.append("Не найдено точное совпадение по контракту, нужен номер контракта или объект.")
    return "\n".join(lines)


def _legal_reply() -> str:
    legal_exists = LEGAL_INDEX_PATH.exists()
    upd_exists = LATEST_LEGAL_UPDATE_PATH.exists()
    lines = [
        "Роль: LEGAL_SHREDDER (протоколы P-002, P-004, P-005)",
        "Правило: неподтвержденные ссылки запрещены, документ отклоняется до исправления.",
        f"Юр-индекс: {'OK' if legal_exists else 'MISSING'} ({LEGAL_INDEX_PATH.relative_to(BASE_DIR)})",
        f"Обновления норм: {'OK' if upd_exists else 'MISSING'} ({LATEST_LEGAL_UPDATE_PATH.relative_to(BASE_DIR)})",
        "Контроль: реквизиты, даты, номер контракта, правовые ссылки.",
    ]
    return "\n".join(lines)


def _finance_reply(contracts: list[Contract]) -> str:
    total = sum(c.price for c in contracts)
    near = sorted([c for c in contracts if c.deadline], key=lambda c: c.deadline)[:5]
    lines = [
        "Роль: FINANCE_CONTROLLER (протоколы P-001, P-002, P-006)",
        f"База контрактов: {len(contracts)}; контрактный портфель: {total:,.2f} RUB".replace(",", " "),
        "Фокус: платежный календарь, кассовые риски, эскалация директору.",
    ]
    if near:
        lines.append("Ближайшие дедлайны:")
        for c in near:
            lines.append(f"- {c.deadline} | {c.object_name} | {c.contract_no}")
    return "\n".join(lines)


def run_crew(user_text: str, agent_name: str, history: list[dict] | None = None) -> str:
    check = validate_required_sources()
    if not check.ok:
        return "\n".join(["Protocol guard failed:"] + [f"- {e}" for e in check.errors])

    contracts = _parse_contracts()
    role = _role_id(agent_name, user_text)

    if role == "pto_engineer":
        return _pto_execution_reply(user_text, contracts)
    if role == "legal_shredder":
        intent = _detect_document_intent(user_text)
        if intent == "claim_letter":
            return _claim_letter_reply(user_text, contracts)
        if intent == "clarification_request":
            return _clarification_request_reply(user_text, contracts)
        if intent == "general_letter":
            return _general_letter_reply(user_text, contracts)
        return _legal_reply()
    if role == "finance_controller":
        return _finance_execution_reply(user_text, contracts)
    return _director_reply(user_text, contracts)
