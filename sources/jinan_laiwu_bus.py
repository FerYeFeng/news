"""Jinan and Laiwu bus announcement source (369 Chuxing)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from urllib.request import Request, urlopen


ENDPOINT = "https://api.369cx.cn/v2/Notice/GetNoticeList"
_CACHE: list[dict] | None = None
_CACHE_LOCK = Lock()


def fetch_all() -> list[dict]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    with _CACHE_LOCK:
        if _CACHE is not None:
            return _CACHE
        return _fetch_all_locked()


def _fetch_all_locked() -> list[dict]:
    global _CACHE
    page_cache: dict[int, list[dict]] = {}

    def fetch_page(page: int) -> list[dict]:
        if page in page_cache:
            return page_cache[page]
        request = Request(f"{ENDPOINT}/{page}", headers={"User-Agent": "Mozilla/5.0"})
        with urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        if int(result.get("status", {}).get("code", -1)) != 0:
            raise RuntimeError(result.get("status", {}).get("msg") or "369 API error")
        page_cache[page] = result.get("result", [])
        return page_cache[page]

    output_dir = Path(__file__).resolve().parents[1] / "html"
    cache_exists = (output_dir / "laiwu-bus.json").exists() and (output_dir / "jinan-bus.json").exists()
    if cache_exists:
        page_items = [fetch_page(0)]
    else:
        low, high = 0, 1
        while fetch_page(high) and high < 256:
            low, high = high, high * 2
        high = min(high, 256)
        while low + 1 < high:
            middle = (low + high) // 2
            if fetch_page(middle):
                low = middle
            else:
                high = middle
        last_page = low
        with ThreadPoolExecutor(max_workers=1) as executor:
            page_items = list(executor.map(fetch_page, range(0, last_page + 1)))

    announcements = []
    for items in page_items:
        for item in items:
            timestamp = int(item.get("time", 0))
            announcements.append(
                {
                    "id": str(item.get("noticeId", "")),
                    "date": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                    "title": item.get("title", ""),
                    "type": item.get("author", "公告"),
                    "image": "",
                    "description": "",
                    "url": item.get("url", ""),
                }
            )
    _CACHE = announcements
    return _CACHE


def fetch_laiwu() -> list[dict]:
    return [item for item in fetch_all() if item.get("type") == "莱芜公交"]


def fetch_jinan() -> list[dict]:
    return [item for item in fetch_all() if item.get("type") == "济南公交"]


LAIWU_SOURCE = {"id": "laiwu-bus", "name": "莱芜公交", "fetch": fetch_laiwu}
JINAN_SOURCE = {"id": "jinan-bus", "name": "济南公交", "fetch": fetch_jinan}
