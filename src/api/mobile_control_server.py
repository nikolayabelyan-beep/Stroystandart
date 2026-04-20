#!/usr/bin/env python3
"""Мобильный API-шлюз для iOS приложения ООО "СТРОЙСТАНДАРТ".

Эндпоинты:
- GET  /health
- GET  /dashboard-url
- GET  /law/latest
- POST /law/update
"""

from __future__ import annotations

import json
import sys
import re
import base64
import threading
import subprocess
import shlex
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.tools.legal_updates_fetcher import run as run_legal_updates
from src.bot.history import add_message, get_history
from src.crew.construction_firm import run_crew

TUNNEL_PATH = BASE_DIR / "data" / "tunnel_url.txt"
LATEST_LAW_PATH = BASE_DIR / "obsidian_vault" / "01_Law" / "Updates" / "LATEST_UPDATES.md"
START_SCRIPT = BASE_DIR / "scripts" / "start_services.sh"
STOP_SCRIPT = BASE_DIR / "scripts" / "stop_services.sh"
DIRECTOR_UPLOADS_DIR = BASE_DIR / "data" / "director_uploads"
DIRECTOR_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
DIRECTOR_CHAT_ID = 990001

UPDATE_STATE = {
    "running": False,
    "started_at": None,
    "finished_at": None,
    "new_publications": None,
    "source_errors": None,
    "report_path": None,
    "error": None,
}
UPDATE_LOCK = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", (name or "").strip())
    cleaned = cleaned.strip("._")
    return cleaned or "upload.bin"


def _director_messages_payload() -> list[dict]:
    history = get_history(DIRECTOR_CHAT_ID)
    out: list[dict] = []
    for i, item in enumerate(history[-80:]):
        role = str(item.get("role", "assistant"))
        content = str(item.get("content", ""))
        created_at = item.get("created_at")
        out.append(
            {
                "id": f"m{i+1}",
                "role": role,
                "content": content,
                "created_at": created_at if isinstance(created_at, str) else None,
            }
        )
    return out


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        payload = json.loads(raw.decode("utf-8"))
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def director_handle_message(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "empty_message"}
    add_message(DIRECTOR_CHAT_ID, "user", text)
    history = get_history(DIRECTOR_CHAT_ID)
    reply = run_crew(text, "Исполнительный Директор", history)
    add_message(DIRECTOR_CHAT_ID, "assistant", reply)
    return {"ok": True, "reply": reply, "messages": _director_messages_payload()}


def director_handle_upload(filename: str, mime_type: str, content_base64: str, note: str) -> dict:
    if not content_base64:
        return {"ok": False, "error": "empty_file"}

    try:
        binary = base64.b64decode(content_base64.encode("utf-8"), validate=True)
    except Exception:
        return {"ok": False, "error": "invalid_base64"}

    if len(binary) > 12 * 1024 * 1024:
        return {"ok": False, "error": "file_too_large"}

    safe_name = _safe_filename(filename)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    save_path = DIRECTOR_UPLOADS_DIR / f"{stamp}_{safe_name}"
    save_path.write_bytes(binary)

    note_clean = (note or "").strip()
    user_prompt = (
        "Пользователь загрузил документ для директора.\n"
        f"Файл: {save_path}\n"
        f"MIME: {(mime_type or 'application/octet-stream').strip()}\n"
        f"Комментарий: {note_clean if note_clean else 'без комментария'}\n"
        "Сформируй директорское решение, риски, и следующий шаг по протоколу."
    )

    add_message(DIRECTOR_CHAT_ID, "user", user_prompt)
    history = get_history(DIRECTOR_CHAT_ID)
    reply = run_crew(user_prompt, "Исполнительный Директор", history)
    add_message(DIRECTOR_CHAT_ID, "assistant", reply)

    return {
        "ok": True,
        "saved_path": str(save_path),
        "reply": reply,
        "messages": _director_messages_payload(),
    }


def _update_worker(timeout: int) -> None:
    try:
        report_path, new_count, error_count = run_legal_updates(timeout)
        with UPDATE_LOCK:
            UPDATE_STATE["running"] = False
            UPDATE_STATE["finished_at"] = now_iso()
            UPDATE_STATE["new_publications"] = new_count
            UPDATE_STATE["source_errors"] = error_count
            UPDATE_STATE["report_path"] = str(report_path)
            UPDATE_STATE["error"] = None
    except Exception as exc:  # noqa: BLE001
        with UPDATE_LOCK:
            UPDATE_STATE["running"] = False
            UPDATE_STATE["finished_at"] = now_iso()
            UPDATE_STATE["error"] = str(exc)


def start_update_background(timeout: int) -> bool:
    with UPDATE_LOCK:
        if UPDATE_STATE["running"]:
            return False
        UPDATE_STATE["running"] = True
        UPDATE_STATE["started_at"] = now_iso()
        UPDATE_STATE["finished_at"] = None
        UPDATE_STATE["new_publications"] = None
        UPDATE_STATE["source_errors"] = None
        UPDATE_STATE["report_path"] = None
        UPDATE_STATE["error"] = None
    thread = threading.Thread(target=_update_worker, args=(timeout,), daemon=True)
    thread.start()
    return True


def snapshot_update_state() -> dict:
    with UPDATE_LOCK:
        return dict(UPDATE_STATE)


def parse_latest_law_report() -> dict:
    if not LATEST_LAW_PATH.exists():
        return {
            "exists": False,
            "new_publications": 0,
            "source_errors": 0,
            "report_path": str(LATEST_LAW_PATH),
            "report_excerpt": "",
        }

    text = LATEST_LAW_PATH.read_text(encoding="utf-8", errors="replace")
    new_match = re.search(r"Новых публикаций:\s*(\d+)", text)
    err_match = re.search(r"Ошибок источников:\s*(\d+)", text)

    return {
        "exists": True,
        "new_publications": int(new_match.group(1)) if new_match else 0,
        "source_errors": int(err_match.group(1)) if err_match else 0,
        "report_path": str(LATEST_LAW_PATH),
        "report_excerpt": "\n".join(text.splitlines()[:20]),
    }


def _run_shell(command: str) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        shell=True,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=25,
    )
    return proc.returncode, (proc.stdout or "").strip()


def _pgrep(pattern: str) -> tuple[int, str]:
    proc = subprocess.run(
        ["pgrep", "-fal", pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=10,
    )
    return proc.returncode, (proc.stdout or "").strip()


def services_status() -> dict:
    api_rc, api_out = _pgrep("mobile_control_server.py --host 0.0.0.0 --port 8787")
    bot_rc, bot_out = _pgrep("src.bot.telegram_app")
    api_sup_rc, api_sup_out = _pgrep("run_api_supervisor.sh")
    bot_sup_rc, bot_sup_out = _pgrep("run_bot_supervisor.sh")
    watchdog_rc, watchdog_out = _pgrep("run_service_watchdog.sh")
    health_ok = False
    try:
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:8787/health", timeout=2) as resp:
            health_ok = resp.status == 200
    except Exception:
        health_ok = False

    return {
        "api_process": bool(api_out.strip()),
        "bot_process": bool(bot_out.strip()),
        "api_supervisor": bool(api_sup_out.strip()),
        "bot_supervisor": bool(bot_sup_out.strip()),
        "watchdog_process": bool(watchdog_out.strip()),
        "api_health": health_ok,
        "api_ps": api_out,
        "bot_ps": bot_out,
        "api_supervisor_ps": api_sup_out,
        "bot_supervisor_ps": bot_sup_out,
        "watchdog_ps": watchdog_out,
        "api_rc": api_rc,
        "bot_rc": bot_rc,
        "api_sup_rc": api_sup_rc,
        "bot_sup_rc": bot_sup_rc,
        "watchdog_rc": watchdog_rc,
    }


def ensure_services() -> dict:
    if not START_SCRIPT.exists():
        return {"ok": False, "error": f"missing start script: {START_SCRIPT}"}
    cmd = shlex.quote(str(START_SCRIPT))
    rc, out = _run_shell(cmd)
    payload = {"ok": rc == 0, "rc": rc, "output": out}
    payload.update(services_status())
    return payload


def restart_services() -> dict:
    # Safe restart endpoint: ensure services are up without interrupting current API request.
    return ensure_services()


class MobileControlHandler(BaseHTTPRequestHandler):
    server_version = "StroyStandartMobileAPI/1.0"

    def _set_headers(self, status: HTTPStatus = HTTPStatus.OK) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._set_headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def log_message(self, fmt: str, *args) -> None:
        return

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._set_headers(HTTPStatus.NO_CONTENT)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._write_json({"ok": True, "service": "mobile_control_server"})
            return

        if parsed.path == "/dashboard-url":
            url = ""
            if TUNNEL_PATH.exists():
                url = TUNNEL_PATH.read_text(encoding="utf-8").strip()
            self._write_json({"dashboard_url": url})
            return

        if parsed.path == "/law/latest":
            self._write_json(parse_latest_law_report())
            return

        if parsed.path == "/services/status":
            payload = {"ok": True}
            payload.update(services_status())
            self._write_json(payload)
            return

        if parsed.path == "/law/update-status":
            payload = {"ok": True}
            payload.update(snapshot_update_state())
            self._write_json(payload)
            return

        if parsed.path == "/director/history":
            self._write_json({"ok": True, "messages": _director_messages_payload()})
            return

        self._write_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/director/message":
            payload = _read_json_body(self)
            text = str(payload.get("text", ""))
            result = director_handle_message(text)
            if not result.get("ok"):
                self._write_json(result, HTTPStatus.BAD_REQUEST)
                return
            self._write_json(result)
            return

        if parsed.path == "/director/upload":
            payload = _read_json_body(self)
            result = director_handle_upload(
                filename=str(payload.get("filename", "")),
                mime_type=str(payload.get("mime_type", "")),
                content_base64=str(payload.get("content_base64", "")),
                note=str(payload.get("note", "")),
            )
            if not result.get("ok"):
                self._write_json(result, HTTPStatus.BAD_REQUEST)
                return
            self._write_json(result)
            return

        if parsed.path == "/services/restart":
            self._write_json(restart_services())
            return

        if parsed.path == "/services/ensure":
            self._write_json(ensure_services())
            return

        if parsed.path != "/law/update":
            self._write_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)
            return

        timeout = 8
        async_mode = True
        qs = parse_qs(parsed.query)
        if "timeout" in qs:
            try:
                timeout = int(qs["timeout"][0])
            except (ValueError, TypeError):
                pass
        if "sync" in qs:
            async_mode = qs["sync"][0] not in ("1", "true", "yes")

        if async_mode:
            started = start_update_background(timeout)
            state = snapshot_update_state()
            payload = {"ok": True, "started": started, "running": state["running"]}
            payload.update(state)
            self._write_json(payload)
            return

        try:
            report_path, new_count, error_count = run_legal_updates(timeout)
            payload = {
                "ok": True,
                "report_path": str(report_path),
                "new_publications": new_count,
                "source_errors": error_count,
            }
            self._write_json(payload)
        except Exception as exc:  # noqa: BLE001
            self._write_json({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Mobile API for iOS control app")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), MobileControlHandler)
    print(f"[OK] Mobile API started: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
