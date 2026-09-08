"""Anqing Palm Bus announcement source."""

from __future__ import annotations

import json
import time
from urllib.request import Request, urlopen


ENDPOINT = "http://223.247.144.152:3003/app-services/notice/public/listAllClass"


def fetch() -> list[dict]:
    url = f"{ENDPOINT}?timestamp={int(time.time() * 1000)}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success"):
        raise RuntimeError(result.get("message") or "Anqing API error")

    announcements = []
    for group in result.get("result", []):
        category = group.get("classify", {}).get("name", "")
        for item in group.get("notice", []):
            announcements.append(
                {
                    "id": str(item.get("id", "")),
                    "date": item.get("createTime", ""),
                    "title": item.get("title", ""),
                    "type": category or "公告",
                    "image": "",
                    "description": item.get("content", ""),
                    "url": item.get("url") or "",
                }
            )
    return announcements


SOURCE = {"id": "anqing-bus", "name": "安庆掌上公交", "fetch": fetch}
