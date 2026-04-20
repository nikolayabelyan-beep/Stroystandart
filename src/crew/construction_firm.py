from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from src.crew.protocol_guard import validate_required_sources

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MASTER_CONTRACTS_PATH = BASE_DIR / "obsidian_vault" / "MASTER_CONTRACTS.md"
MY_COMPANY_PATH = BASE_DIR / "obsidian_vault" / "MY_COMPANY.md"
PROTOCOLS_PATH = BASE_DIR / "obsidian_vault" / "02_Protocols" / "AI_OFFICE_PROTOCOLS.md"
TEMPLATES_INDEX_PATH = BASE_DIR / "obsidian_vault" / "02_Protocols" / "DOCUMENT_TEMPLATES_INDEX.md"
LEGAL_INDEX_PATH = BASE_DIR / "obsidian_vault" / "01_Law" / "LEGAL_REFERENCE_INDEX.md"
LATEST_LEGAL_UPDATE_PATH = BASE_DIR / "obsidian_vault" / "01_Law" / "Updates" / "LATEST_UPDATES.md"


@dataclass
class Contract:
    object_name: str
    customer: str
    contract_info: str
    contract_no: str
    price: float
    deadline: str


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


def _role_id(agent_name: str, user_text: str) -> str:
    name = (agent_name or "").lower()
    text = (user_text or "").lower()

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
        return _pto_reply(user_text, contracts)
    if role == "legal_shredder":
        return _legal_reply()
    if role == "finance_controller":
        return _finance_reply(contracts)
    return _director_reply(user_text, contracts)
