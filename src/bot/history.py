from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
HISTORY_DIR = BASE_DIR / "data" / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def _path(chat_id: int) -> Path:
    return HISTORY_DIR / f"{chat_id}.json"


def get_history(chat_id: int) -> list[dict]:
    path = _path(chat_id)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def add_message(chat_id: int, role: str, content: str) -> None:
    history = get_history(chat_id)
    history.append({"role": role, "content": content})
    # Keep last 80 messages to avoid unlimited growth.
    history = history[-80:]
    _path(chat_id).write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_history(chat_id: int) -> None:
    path = _path(chat_id)
    if path.exists():
        path.unlink()
