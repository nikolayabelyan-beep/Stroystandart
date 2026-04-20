from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = BASE_DIR / "data" / "agents" / "agents_registry.json"


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]


def _load_registry() -> dict:
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry not found: {REGISTRY_PATH}")
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def validate_required_sources() -> ValidationResult:
    payload = _load_registry()
    errors: list[str] = []
    for rel_path in payload.get("mandatory_data_sources", []):
        abs_path = BASE_DIR / rel_path
        if not abs_path.exists():
            errors.append(f"Missing required source: {rel_path}")
    return ValidationResult(ok=not errors, errors=errors)


def role_exists(role_id: str) -> bool:
    payload = _load_registry()
    return any(role.get("id") == role_id for role in payload.get("roles", []))


def role_protocols(role_id: str) -> list[str]:
    payload = _load_registry()
    for role in payload.get("roles", []):
        if role.get("id") == role_id:
            return role.get("must_follow_protocols", [])
    return []
