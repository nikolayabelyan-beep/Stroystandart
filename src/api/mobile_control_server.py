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
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.tools.legal_updates_fetcher import run as run_legal_updates

TUNNEL_PATH = BASE_DIR / "data" / "tunnel_url.txt"
LATEST_LAW_PATH = BASE_DIR / "obsidian_vault" / "01_Law" / "Updates" / "LATEST_UPDATES.md"

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

        if parsed.path == "/law/update-status":
            payload = {"ok": True}
            payload.update(snapshot_update_state())
            self._write_json(payload)
            return

        self._write_json({"error": "not_found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
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
