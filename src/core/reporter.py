from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MASTER_CONTRACTS_PATH = BASE_DIR / "obsidian_vault" / "MASTER_CONTRACTS.md"
LATEST_LEGAL_UPDATE_PATH = BASE_DIR / "obsidian_vault" / "01_Law" / "Updates" / "LATEST_UPDATES.md"


@dataclass
class Contract:
    object_name: str
    contract_no: str
    price: float
    deadline: str


class BusinessReporter:
    def _read(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")

    def _parse_money(self, text: str) -> float:
        cleaned = text.replace("₽", "").replace(" ", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _parse_contracts(self) -> list[Contract]:
        content = self._read(MASTER_CONTRACTS_PATH)
        pattern = re.compile(r"###\s+\d+\.\s+Объект:\s+(.+?)\n([\s\S]*?)(?=\n---|\n###\s+\d+\.|$)")
        contracts: list[Contract] = []
        for object_name_raw, block in pattern.findall(content):
            contract_m = re.search(r"\*\s*\*\*Контракт:\*\*\s*(.+)", block)
            price_m = re.search(r"\*\s*\*\*Цена контракта:\*\*\s*(.+)", block)
            deadline_m = re.search(r"\*\s*\*\*Срок исполнения:\*\*\s*(.+)", block)
            contract_info = contract_m.group(1).strip() if contract_m else ""
            contract_no = re.sub(r"^№\s*", "", contract_info)
            contract_no = re.sub(r"\s+от\s+\d{2}\.\d{2}\.\d{4}$", "", contract_no).strip()
            contracts.append(
                Contract(
                    object_name=object_name_raw.strip(),
                    contract_no=contract_no,
                    price=self._parse_money(price_m.group(1).strip() if price_m else "0"),
                    deadline=deadline_m.group(1).strip() if deadline_m else "",
                )
            )
        return contracts

    def _latest_legal_status(self) -> str:
        text = self._read(LATEST_LEGAL_UPDATE_PATH)
        if not text:
            return "no legal updates report"
        new_m = re.search(r"Новых публикаций:\s*(\d+)", text)
        err_m = re.search(r"Ошибок источников:\s*(\d+)", text)
        new = new_m.group(1) if new_m else "0"
        err = err_m.group(1) if err_m else "0"
        return f"new={new}, source_errors={err}"

    def generate_morning_report(self, is_monday: bool = False) -> str:
        contracts = self._parse_contracts()
        total = sum(c.price for c in contracts)
        top = sorted(contracts, key=lambda x: x.price, reverse=True)[:3]
        lines = [
            "*Morning report*",
            f"Contracts in registry: {len(contracts)}",
            f"Total portfolio: {total:,.2f} RUB".replace(",", " "),
            f"Legal updates: {self._latest_legal_status()}",
            "Top contracts by amount:",
        ]
        for c in top:
            lines.append(f"- {c.object_name}: {c.price:,.2f} RUB".replace(",", " "))
        if is_monday:
            lines.append("Monday mode: include weekly planning review.")
        return "\n".join(lines)

    def generate_evening_report(self) -> str:
        contracts = self._parse_contracts()
        soon = sorted([c for c in contracts if c.deadline], key=lambda c: c.deadline)[:5]
        lines = [
            "*Evening report*",
            f"Active contracts tracked: {len(contracts)}",
            "Nearest deadlines:",
        ]
        for c in soon:
            lines.append(f"- {c.deadline}: {c.object_name} ({c.contract_no})")
        lines.append(f"Legal updates: {self._latest_legal_status()}")
        return "\n".join(lines)
