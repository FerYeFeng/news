"""Scraper for Mianyang Bus route adjustment announcements."""

from __future__ import annotations

import html
import re
from urllib.parse import urljoin
from urllib.request import Request, urlopen


BASE_URL = "https://www.mybus.cn/"
LIST_URL = urljoin(BASE_URL, "xianludiaozheng/")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BusNoticeMonitor/1.0)"}


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def fetch_html(url: str) -> str:
    with urlopen(Request(url, headers=HEADERS), timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch() -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    page_url = LIST_URL
    for _ in range(30):
        body = fetch_html(page_url)
        matches = re.findall(
            r'<a\s+href=["\']([^"\']*?/fuwudating/\d+\.html)["\'][^>]*>\s*'
            r'<div[^>]*>\s*<p[^>]*>(.*?)</p>\s*<div[^>]*>([^<]+)</div>',
            body,
            flags=re.I | re.S,
        )
        for href, title, published in matches:
            detail_url = urljoin(BASE_URL, href)
            if detail_url in seen:
                continue
            seen.add(detail_url)
            description = ""
            try:
                detail = fetch_html(detail_url)
                content = re.search(r'<div[^>]+class=["\']newsContent-in["\'][^>]*>(.*?)</div>\s*</div>', detail, re.I | re.S)
                description = clean(content.group(1)) if content else ""
            except Exception:
                pass
            items.append({
                "id": detail_url.rsplit("/", 1)[-1].split(".", 1)[0],
                "date": clean(published),
                "title": clean(title),
                "type": "线路调整",
                "description": description,
                "url": detail_url,
            })
        next_match = re.search(r'href=["\']([^"\']*?/xianludiaozheng/list_22_\d+/)["\'][^>]*>\s*下一页', body, re.I)
        if not next_match:
            break
        next_url = urljoin(BASE_URL, next_match.group(1))
        if next_url == page_url:
            break
        page_url = next_url
    return items


SOURCE = {"id": "mianzhou-bus", "fetch": fetch, "allow_empty": True}
