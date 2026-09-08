"""Yangzhou Palm Bus announcement source."""

from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENDPOINT = "http://61.132.33.218:85/prod-api/infomanage/app/client/routesDynamic/list"


def fetch_page(page: int, page_size: int) -> dict:
    query = urlencode({"routeName": "", "pageNum": page, "pageSize": page_size})
    request = Request(f"{ENDPOINT}?{query}", headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch() -> list[dict]:
    page_size = 100
    first = fetch_page(1, page_size)
    if int(first.get("code", 0)) != 200:
        raise RuntimeError(first.get("msg") or "Yangzhou API error")
    rows = list(first.get("rows", []))
    total = int(first.get("total", len(rows)))
    for page in range(2, (total + page_size - 1) // page_size + 1):
        rows.extend(fetch_page(page, page_size).get("rows", []))

    return [
        {
            "id": str(item.get("id", "")),
            "date": item.get("publicDate", ""),
            "title": item.get("title", ""),
            "type": item.get("statusName", "公告"),
            "image": item.get("coverPic", ""),
            "description": "",
            "url": "",
        }
        for item in rows
    ]


SOURCE = {"id": "yangzhou-bus", "name": "扬州掌上公交", "fetch": fetch}
