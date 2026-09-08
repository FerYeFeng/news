"""Taizhou Hao Chuxing announcement source."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


BASE_URL = "https://taizhou.nandasoft-its.com:8887"
LIST_URL = f"{BASE_URL}/tzhcx/notice/toList?type=1"
PAGE_URL = f"{BASE_URL}/tzhcx/notice/toListPage"


class NoticeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.total = 0
        self.items: list[dict] = []
        self.current: dict | None = None
        self.capture: str | None = None
        self.buffer: list[str] = []
        self.spans: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = (values.get("class") or "").split()
        if tag == "input" and values.get("id") == "total":
            try:
                self.total = int(values.get("value") or 0)
            except ValueError:
                self.total = 0
        elif tag == "li" and "dataList" in classes:
            self.current = {"url": "", "title": ""}
            self.spans = []
        elif self.current is not None and tag == "a":
            self.current["url"] = urljoin(BASE_URL, values.get("href") or "")
            self.capture = "title"
            self.buffer = []
        elif self.current is not None and tag == "span":
            self.capture = "span"
            self.buffer = []

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.current is None:
            return
        if tag == "a" and self.capture == "title":
            self.current["title"] = "".join(self.buffer).strip()
            self.capture = None
        elif tag == "span" and self.capture == "span":
            self.spans.append("".join(self.buffer).strip())
            self.capture = None
        elif tag == "li":
            date_value = next((value for value in reversed(self.spans) if value), "")
            self.current["date"] = date_value
            self.items.append(self.current)
            self.current = None


def request_html(url: str, data: bytes | None = None) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
    request = Request(url, data=data, headers=headers)
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def parse_page(document: str) -> NoticeParser:
    parser = NoticeParser()
    parser.feed(document)
    return parser


def fetch() -> list[dict]:
    first = parse_page(request_html(LIST_URL))
    raw_items = list(first.items)
    total = first.total or len(raw_items)
    page_size = 20
    cache_exists = (Path(__file__).resolve().parents[1] / "html" / "taizhou-bus.json").exists()
    pages = range(2, (total + page_size - 1) // page_size + 1) if not cache_exists else []

    def load_page(page: int) -> list[dict]:
        payload = urlencode({"type": "1", "page": page, "limit": page_size}).encode()
        return parse_page(request_html(PAGE_URL, payload)).items

    with ThreadPoolExecutor(max_workers=8) as executor:
        for items in executor.map(load_page, pages):
            raw_items.extend(items)

    announcements = []
    for item in raw_items:
        item_id = item["url"].split("id=", 1)[-1].split("&", 1)[0]
        announcements.append(
            {
                "id": item_id,
                "date": item.get("date", ""),
                "title": item.get("title", ""),
                "type": "HTML",
                "image": "",
                "description": "",
                "url": item.get("url", ""),
            }
        )
    return announcements


SOURCE = {"id": "taizhou-bus", "name": "泰州好出行", "fetch": fetch}
