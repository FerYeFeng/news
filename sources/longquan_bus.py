"""Longquanyi bus announcement source."""

from __future__ import annotations

import json
from urllib.request import Request, urlopen


ENDPOINT = (
    "http://125.71.239.27:8001/BusService/Query_ByNewInfoSummary/"
    "?UseFor=0&timeStamp=20260914135510&Random=685"
    "&SignKey=1a6c8bcc38ed030258824ce2b320c5d90623d9a98d291ff17d62ee89c410db34"
    "&PackageName=com.hisen"
)


def fetch() -> list[dict]:
    request = Request(ENDPOINT, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=30) as response:
        body = response.read()
    if not body:
        raise RuntimeError("龙泉公交接口未返回内容，签名可能已失效")
    result = json.loads(body.decode("utf-8"))
    if not isinstance(result, list):
        raise RuntimeError("龙泉公交接口返回异常")
    return [
        {
            "id": str(item.get("ID", "")),
            "date": item.get("RealeaseTime", ""),
            "title": item.get("Title", ""),
            "type": "公交公告",
            "description": item.get("Summary", ""),
            "url": "",
        }
        for item in result
    ]


SOURCE = {"id": "longquan-bus", "fetch": fetch, "allow_empty": True}
