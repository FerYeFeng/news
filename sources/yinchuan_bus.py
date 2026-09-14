"""Scraper for Yinchuan government public-transport announcements."""

from __future__ import annotations

import html
import re
from urllib.parse import urljoin
from urllib.request import Request, urlopen


LIST_URL = "https://www.yinchuan.gov.cn/xxgk/zdlyxxgk/szfw/gj/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; BusNoticeMonitor/1.0)"}


def clean(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def fetch_html(url: str) -> str:
    with urlopen(Request(url, headers=HEADERS), timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch() -> list[dict]:
    body = fetch_html(LIST_URL)
    items = []
    seen = set()
    for href, title in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', body, re.I | re.S):
        title = clean(title)
        if not title or not re.search(r"公交|线路|调整|通告", title):
            continue
        detail_url = urljoin(LIST_URL, href)
        if detail_url in seen:
            continue
        seen.add(detail_url)
        date_match = re.search(r"t(20\d{6,8})", href)
        raw_date = date_match.group(1) if date_match else ""
        published = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:]}" if len(raw_date) == 8 else ""
        description = ""
        try:
            detail = fetch_html(detail_url)
            match = re.search(r'<div[^>]+class=["\'][^"\']*(?:TRS_Editor|article|content)[^"\']*["\'][^>]*>(.*?)</div>', detail, re.I | re.S)
            if match:
                description = clean(match.group(1))
        except Exception:
            pass
        items.append({"id": detail_url.rsplit("/", 1)[-1].split(".", 1)[0], "date": published,
                      "title": title, "type": "公交线路公告", "description": description, "url": detail_url})
    return items


SOURCE = {"id": "yinchuan-bus", "fetch": fetch, "allow_empty": True}
