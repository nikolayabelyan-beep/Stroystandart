#!/usr/bin/env python3
"""Fetcher обновлений юридической базы из официальных источников.

Принципы:
- Никаких выдуманных норм: в отчет попадают только найденные публикации с URL.
- Дедупликация по ссылке/заголовку через state.json.
- Без внешних зависимостей (stdlib only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Iterable
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SOURCES_PATH = BASE_DIR / "data" / "legal_updates" / "sources.json"
STATE_PATH = BASE_DIR / "data" / "legal_updates" / "state.json"
UPDATES_DIR = BASE_DIR / "obsidian_vault" / "01_Law" / "Updates"
LATEST_PATH = UPDATES_DIR / "LATEST_UPDATES.md"

DEFAULT_TIMEOUT_SECONDS = 25
MAX_ITEMS_PER_SOURCE = 25
USER_AGENT = "StroyStandartLegalUpdater/1.0"


@dataclass
class Source:
    source_id: str
    name: str
    url: str
    kind: str
    tags: list[str]


@dataclass
class Item:
    source_id: str
    source_name: str
    title: str
    link: str
    published: str
    summary: str

    @property
    def fingerprint(self) -> str:
        raw = f"{self.source_id}|{self.link}|{self.title}".encode("utf-8", errors="ignore")
        return hashlib.sha256(raw).hexdigest()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_sources(path: Path) -> list[Source]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources: list[Source] = []
    for entry in payload:
        sources.append(
            Source(
                source_id=entry["id"],
                name=entry["name"],
                url=entry["url"],
                kind=entry.get("kind", "html"),
                tags=entry.get("tags", []),
            )
        )
    return sources


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"seen": {}, "last_run_at": None}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"seen": {}, "last_run_at": None}


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_url(url: str, timeout: int) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    with urlopen(request, timeout=timeout, context=context) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read()
    return raw.decode(charset, errors="replace")


def strip_html(text: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", text)
    normalized = re.sub(r"\s+", " ", no_tags).strip()
    return unescape(normalized)


def parse_rss_like(source: Source, body: str) -> list[Item]:
    items: list[Item] = []
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError:
        return items

    # RSS
    for node in root.findall(".//item")[:MAX_ITEMS_PER_SOURCE]:
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        published = (node.findtext("pubDate") or "").strip()
        summary = strip_html(node.findtext("description") or "")
        if title and link:
            items.append(Item(source.source_id, source.name, title, link, published, summary))

    # Atom
    if not items:
        namespace = {"atom": "http://www.w3.org/2005/Atom"}
        for node in root.findall(".//atom:entry", namespace)[:MAX_ITEMS_PER_SOURCE]:
            title = (node.findtext("atom:title", default="", namespaces=namespace) or "").strip()
            published = (
                node.findtext("atom:updated", default="", namespaces=namespace)
                or node.findtext("atom:published", default="", namespaces=namespace)
            ).strip()
            link_node = node.find("atom:link", namespace)
            link = ""
            if link_node is not None:
                link = (link_node.attrib.get("href") or "").strip()
            summary = strip_html(
                node.findtext("atom:summary", default="", namespaces=namespace)
                or node.findtext("atom:content", default="", namespaces=namespace)
            )
            if title and link:
                items.append(Item(source.source_id, source.name, title, link, published, summary))

    return items


def parse_html_fallback(source: Source, body: str) -> list[Item]:
    # Универсальный fallback: извлекаем теги <a href="...">текст</a>
    # и фильтруем слишком короткие/служебные значения.
    items: list[Item] = []
    anchor_pattern = re.compile(r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
    seen_links: set[str] = set()

    for href, text in anchor_pattern.findall(body):
        title = strip_html(text)
        if not title or len(title) < 12:
            continue
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue

        if href.startswith("/"):
            link = source.url.rstrip("/") + href
        elif href.startswith("http"):
            link = href
        else:
            link = source.url.rstrip("/") + "/" + href.lstrip("/")

        # Только внутренние ссылки источника
        if source.url.split("//", 1)[-1].split("/", 1)[0] not in link:
            continue
        if link in seen_links:
            continue

        seen_links.add(link)
        items.append(Item(source.source_id, source.name, title, link, "", ""))
        if len(items) >= MAX_ITEMS_PER_SOURCE:
            break

    return items


def fetch_source_items(source: Source, timeout: int) -> tuple[list[Item], str | None]:
    try:
        body = fetch_url(source.url, timeout)
    except (HTTPError, URLError, TimeoutError, ssl.SSLError, OSError) as exc:
        return [], f"{type(exc).__name__}: {exc}"

    as_rss = parse_rss_like(source, body)
    if as_rss:
        return as_rss, None

    as_html = parse_html_fallback(source, body)
    return as_html, None


def filter_new(items: Iterable[Item], state: dict) -> list[Item]:
    seen = state.setdefault("seen", {})
    new_items: list[Item] = []
    for item in items:
        fp = item.fingerprint
        if fp in seen:
            continue
        seen[fp] = {
            "source": item.source_name,
            "title": item.title,
            "link": item.link,
            "published": item.published,
            "seen_at": now_utc_iso(),
        }
        new_items.append(item)
    return new_items


def build_report(run_at: datetime, new_items: list[Item], errors: list[str]) -> str:
    date_human = run_at.strftime("%d.%m.%Y %H:%M:%S UTC")
    lines: list[str] = []
    lines.append(f"# Обновление правовой базы от {date_human}")
    lines.append("")
    lines.append("## Результат")
    lines.append(f"- Новых публикаций: {len(new_items)}")
    lines.append(f"- Ошибок источников: {len(errors)}")
    lines.append("")

    lines.append("## Новые публикации")
    if not new_items:
        lines.append("- Новые публикации не обнаружены.")
    else:
        for item in new_items:
            title = item.title.replace("\n", " ").strip()
            meta = f" ({item.published})" if item.published else ""
            lines.append(f"- [{title}]({item.link}){meta} — `{item.source_name}`")

    lines.append("")
    lines.append("## Ошибки источников")
    if not errors:
        lines.append("- Нет")
    else:
        for err in errors:
            lines.append(f"- {err}")

    lines.append("")
    lines.append("## Важно")
    lines.append("- Этот отчет не является юридическим заключением.")
    lines.append("- LEGAL_SHREDDER должен ссылаться только на официальные публикации из списка выше.")
    return "\n".join(lines) + "\n"


def write_reports(content: str, run_at: datetime) -> Path:
    UPDATES_DIR.mkdir(parents=True, exist_ok=True)
    stamp = run_at.strftime("%Y-%m-%d_%H-%M")
    output_path = UPDATES_DIR / f"{stamp}_legal_updates.md"
    output_path.write_text(content, encoding="utf-8")
    LATEST_PATH.write_text(content, encoding="utf-8")
    return output_path


def prune_state(state: dict, keep_last: int = 5000) -> None:
    seen = state.get("seen", {})
    if len(seen) <= keep_last:
        return
    # сохраняем только последние записи по seen_at
    ordered = sorted(
        seen.items(),
        key=lambda kv: kv[1].get("seen_at", ""),
        reverse=True,
    )
    state["seen"] = dict(ordered[:keep_last])


def run(timeout: int) -> tuple[Path, int, int]:
    sources = load_sources(SOURCES_PATH)
    state = load_state(STATE_PATH)

    collected: list[Item] = []
    errors: list[str] = []

    for source in sources:
        items, err = fetch_source_items(source, timeout)
        if err:
            errors.append(f"{source.name}: {err}")
            continue
        collected.extend(items)

    new_items = filter_new(collected, state)
    state["last_run_at"] = now_utc_iso()
    prune_state(state)
    save_state(STATE_PATH, state)

    run_at = datetime.now(timezone.utc)
    report = build_report(run_at, new_items, errors)
    report_path = write_reports(report, run_at)
    return report_path, len(new_items), len(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description="Обновление юридической базы из официальных источников")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="Таймаут запроса в секундах")
    args = parser.parse_args()

    try:
        report_path, new_count, error_count = run(timeout=args.timeout)
    except FileNotFoundError as exc:
        print(f"[ERROR] Не найден файл конфигурации: {exc}")
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] Непредвиденная ошибка: {exc}")
        return 2

    print(f"[OK] Отчет: {report_path}")
    print(f"[OK] Новых публикаций: {new_count}")
    print(f"[OK] Ошибок источников: {error_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
