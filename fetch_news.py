#!/usr/bin/env python3
"""Fetch announcements from all configured bus operators and build HTML."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import html
import json
import sys
from datetime import date, datetime
from pathlib import Path

from sources import SOURCES


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "html"
PAGE_SIZE = 30


def parse_date(value: str) -> date:
    for pattern in ("%Y年%m月%d日", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value.strip(), pattern).date()
        except ValueError:
            pass
    return date.min


def normalize(source: dict, items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        item_id = str(item.get("id", "")).strip()
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        result.append({**item, "sourceId": source["id"], "sourceName": source["name"]})
    return sorted(
        result,
        key=lambda item: (parse_date(str(item.get("date", ""))), str(item.get("title", ""))),
        reverse=True,
    )


def render_page(
    title: str,
    items: list[dict],
    source_links: list[tuple[str, str, str]],
    page: int,
    page_count: int,
    total_items: int,
    base_name: str,
    notice: str = "",
) -> str:
    links = ""
    for name, path, status in source_links:
        suffix = "（暂无录入）" if status == "missing" else "（更新失败）" if status == "error" else ""
        class_name = f' class="{status}"' if status else ""
        links += f'<a href="{html.escape(path, quote=True)}"{class_name}>{html.escape(name + suffix)}</a>'
    rows = []
    for item in items:
        image = str(item.get("image", ""))
        url = str(item.get("url", ""))
        title_text = html.escape(str(item.get("title", "")))
        title_cell = (
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noreferrer">{title_text}</a>'
            if url
            else title_text
        )
        description = str(item.get("description", "")).strip()
        if description:
            title_cell += (
                "<details><summary>查看正文</summary>"
                f'<div class="description">{html.escape(description)}</div></details>'
            )
        image_link = (
            f'<a href="{html.escape(image, quote=True)}" target="_blank" rel="noreferrer">查看</a>'
            if image
            else ""
        )
        rows.append(
            "<tr>"
            f"<td>{html.escape(str(item.get('date', '')))}</td>"
            f"<td>{html.escape(str(item.get('sourceName', '')))}</td>"
            f"<td>{title_cell}</td>"
            f"<td>{html.escape(str(item.get('type', '')))}</td>"
            f"<td>{image_link}</td>"
            "</tr>"
        )
    if not rows:
        empty_text = "暂无录入该平台" if "暂无录入该平台" in title else "暂无公告"
        rows.append(f'<tr><td colspan="5" class="empty">{empty_text}</td></tr>')
    fetched_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    previous_link = base_name if page == 2 else f"{Path(base_name).stem}-{page - 1}.html"
    next_link = f"{Path(base_name).stem}-{page + 1}.html"
    pagination = '<div class="pagination">'
    if page > 1:
        pagination += f'<a href="{previous_link}">上一页</a>'
    pagination += f'<span>第 {page} / {page_count} 页</span>'
    if page < page_count:
        pagination += f'<a href="{next_link}">下一页</a>'
    pagination += "</div>"
    notice_html = f'<div class="error-banner">{html.escape(notice)}</div>' if notice else ""
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="180">
<title>{html.escape(title)}</title>
<style>
:root{{--line:#d8dee4;--muted:#59636e;--head:#f6f8fa;--link:#0969da}}
*{{box-sizing:border-box}}body{{font-family:"Microsoft YaHei",Arial,sans-serif;margin:0;color:#1f2328}}
header{{padding:20px 24px 14px;border-bottom:1px solid var(--line);background:#fff}}
h1{{font-size:22px;margin:0 0 8px}}p{{color:var(--muted);margin:0}}nav{{margin-top:12px;display:flex;flex-wrap:wrap;gap:8px 14px;max-width:100%}}
nav a{{overflow-wrap:anywhere;word-break:break-word}}
a{{color:var(--link);text-decoration:none}}main{{padding:16px 24px 32px}}table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}}th{{background:var(--head)}}
td:first-child{{white-space:nowrap}}tr:nth-child(even){{background:#fbfcfd}}
details{{margin-top:7px}}summary{{color:var(--link);cursor:pointer}}.description{{white-space:pre-wrap;margin-top:7px;line-height:1.7;color:#3d444d}}
.pagination{{display:flex;align-items:center;justify-content:center;gap:18px;margin:16px 0}}.pagination a{{font-weight:600}}
nav .missing{{color:#6e7781}}nav .error{{color:#cf222e;font-weight:700}}.empty{{padding:28px;text-align:center;color:var(--muted)}}
.error-banner{{margin-top:12px;padding:10px 12px;border:1px solid #ff8182;background:#ffebe9;color:#82071e}}
@media(max-width:700px){{header,main{{padding-left:12px;padding-right:12px}}th:nth-child(4),td:nth-child(4),th:nth-child(5),td:nth-child(5){{display:none}}}}
</style></head><body><header><h1>{html.escape(title)}</h1>
<p>共 {total_items} 条，每页最多 {PAGE_SIZE} 条，按日期从新到旧排列。更新时间：{fetched_at}</p>{notice_html}<nav>{links}</nav></header>
<main><table><thead><tr><th>日期</th><th>公交</th><th>公告标题</th><th>类型</th><th>图片</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>{pagination}</main></body></html>"""


def write_paginated_pages(
    base_name: str,
    title: str,
    items: list[dict],
    source_links: list[tuple[str, str, str]],
    notice: str = "",
) -> None:
    stem = Path(base_name).stem
    for stale_path in OUTPUT_DIR.glob(f"{stem}-[0-9]*.html"):
        stale_path.unlink()
    page_count = max(1, (len(items) + PAGE_SIZE - 1) // PAGE_SIZE)
    for page in range(1, page_count + 1):
        page_items = items[(page - 1) * PAGE_SIZE:page * PAGE_SIZE]
        filename = base_name if page == 1 else f"{stem}-{page}.html"
        (OUTPUT_DIR / filename).write_text(
            render_page(title, page_items, source_links, page, page_count, len(items), base_name, notice),
            encoding="utf-8",
        )


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_items = []
    source_results = []

    def update_source(source: dict) -> tuple[dict, list[dict], str]:
        if source.get("unavailable"):
            return source, [], ""
        cache_path = OUTPUT_DIR / f"{source['id']}.json"
        cached_items = []
        if cache_path.exists():
            try:
                cached_items = json.loads(cache_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                cached_items = []
        try:
            fetched_items = source["fetch"]()
        except Exception as exc:
            fetched_items = []
            cache_note = "，使用历史缓存" if cached_items else "，暂无历史缓存"
            warning = f"抓取失败{cache_note}：{source['name']}：{exc}"
        else:
            warning = ""
        items = normalize(source, fetched_items + cached_items)
        return {**source, "fetch_error": warning}, items, warning

    with ThreadPoolExecutor(max_workers=min(32, len(SOURCES))) as executor:
        updates = list(executor.map(update_source, SOURCES))

    for source, items, warning in updates:
        if warning:
            print(warning, file=sys.stderr)
        all_items.extend(items)
        source_results.append((source, items))
        print(f"{source['name']}：{len(items)} 条")

    source_links = [("全部公交", "index.html", "")] + [
        (source["name"], f"{source['id']}.html",
         "missing" if source.get("unavailable") else "error" if source.get("fetch_error") else "")
        for source, _ in source_results
    ]
    for source, items in source_results:
        filename = f"{source['id']}.html"
        title = f"{source['name']}公告"
        if source.get("unavailable"):
            title += "（暂无录入该平台）"
        write_paginated_pages(filename, title, items, source_links, source.get("fetch_error", ""))
        (OUTPUT_DIR / f"{source['id']}.json").write_text(
            json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    all_items.sort(
        key=lambda item: (parse_date(str(item.get("date", ""))), str(item.get("title", ""))),
        reverse=True,
    )
    write_paginated_pages("index.html", "公交公告汇总", all_items, source_links)
    (OUTPUT_DIR / "all.json").write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"合计：{len(all_items)} 条")
    print(f"HTML：{OUTPUT_DIR / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
