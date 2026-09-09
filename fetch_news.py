#!/usr/bin/env python3
"""Fetch bus announcements and build one responsive HTML application."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import shutil
import sys
from datetime import date, datetime, time as dt_time
from pathlib import Path

from sources import SOURCES, AI_SOURCE_IDS


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "html"


def parse_date(value: str) -> date:
    for pattern in ("%Y年%m月%d日", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            pass
    return date.min


def sort_key(item: dict) -> tuple:
    value = str(item.get("date", "")).strip()
    for pattern in (
        "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S",
        "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
        "%Y年%m月%d日 %H:%M:%S", "%Y年%m月%d日 %H:%M",
    ):
        try:
            parsed = datetime.strptime(value, pattern)
            return parsed.date(), 1, parsed.time(), str(item.get("title", ""))
        except ValueError:
            pass
    return parse_date(value), 0, dt_time.min, str(item.get("title", ""))


def normalize(source: dict, items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        item_id = str(item.get("id", "")).strip()
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        result.append({**item, "sourceId": source["id"], "sourceName": source["name"]})
    return sorted(result, key=sort_key, reverse=True)


def clean_old_html() -> None:
    for path in OUTPUT_DIR.glob("*.html"):
        if path.name != "index.html":
            path.unlink()


def copy_frontend() -> None:
    clean_old_html()
    for name in ("index.html", "styles.css", "app.js"):
        shutil.copyfile(ROOT / "web" / name, OUTPUT_DIR / name)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_items: list[dict] = []
    source_results: list[tuple[dict, list[dict]]] = []

    def update_source(source: dict) -> tuple[dict, list[dict], str]:
        if source.get("unavailable"):
            return {**source, "status": "missing", "notice": "尚未录入抓取接口"}, [], ""
        cache_path = OUTPUT_DIR / f"{source['id']}.json"
        try:
            cached_items = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else []
        except (OSError, json.JSONDecodeError):
            cached_items = []
        try:
            fetched_items = source["fetch"]()
            if not isinstance(fetched_items, list):
                raise RuntimeError("接口未返回公告列表")
            fetched_items = [item for item in fetched_items if isinstance(item, dict) and str(item.get("title", "")).strip()]
        except Exception as exc:
            fetched_items = []
            cache_note = "，使用历史缓存" if cached_items else "，暂无历史缓存"
            notice = f"抓取失败{cache_note}：{exc}"
            result_source = {**source, "status": "error", "notice": notice}
        else:
            if fetched_items:
                result_source = {**source, "status": "ok", "notice": ""}
            else:
                cache_note = "，使用历史缓存" if cached_items else ""
                notice = f"公告内容为空{cache_note}"
                result_source = {**source, "status": "empty", "notice": notice}
        items = normalize(source, fetched_items + cached_items)
        return result_source, items, result_source.get("notice", "")

    with ThreadPoolExecutor(max_workers=min(32, len(SOURCES))) as executor:
        updates = list(executor.map(update_source, SOURCES))

    today = datetime.now().date()
    yesterday = today.fromordinal(today.toordinal() - 1)
    statuses = []
    for source, items, warning in updates:
        if warning and source.get("status") != "missing":
            print(f"{source['name']}：{warning}", file=sys.stderr)
        all_items.extend(items)
        source_results.append((source, items))
        dates = {parse_date(str(item.get("date", ""))) for item in items}
        recency = "today" if today in dates else "yesterday" if yesterday in dates else "older"
        statuses.append({
            "id": source["id"], "name": source["name"], "city": source.get("city", ""),
            "platform": source.get("platform", ""), "status": source.get("status", "ok"),
            "notice": source.get("notice", ""), "count": len(items), "recency": recency,
            "ai": source["id"] in AI_SOURCE_IDS,
        })
        (OUTPUT_DIR / f"{source['id']}.json").write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{source['name']}：{len(items)} 条")

    all_items.sort(key=sort_key, reverse=True)
    fetched_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    (OUTPUT_DIR / "all.json").write_text(json.dumps(all_items, ensure_ascii=False), encoding="utf-8")
    (OUTPUT_DIR / "sources-status.json").write_text(
        json.dumps({"updatedAt": fetched_at, "totalItems": len(all_items), "sources": statuses}, ensure_ascii=False),
        encoding="utf-8",
    )
    copy_frontend()
    print(f"合计：{len(all_items)} 条")
    print(f"HTML：{OUTPUT_DIR / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
