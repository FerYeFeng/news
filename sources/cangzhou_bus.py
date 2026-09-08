"""Cangzhou Xing bus announcement source."""

from __future__ import annotations

import hashlib
import json
import ssl
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENDPOINT = "https://app.cangzhoubus.com:8880/"
PAYLOAD = {
    "appId": "pdbmiyhm95tm",
    "appVersion": "2.4.3",
    "cityCode": "czh",
    "deviceBrand": "Xiaomi",
    "deviceId": "69f7f556-ae5c-4710-b4f0-efa18fa3351b",
    "deviceModel": "24129PN74C",
    "from": 1,
    "lat": 0.0,
    "lng": 0.0,
    "reqType": "CommonService",
}


def signed_payload() -> dict:
    payload = {**PAYLOAD, "timestamp": int(time.time() * 1000)}
    canonical = urlencode(sorted(payload.items()))
    payload["sign"] = hashlib.md5(
        f"{canonical}&key=dalianyitongchuangxin".encode("utf-8")
    ).hexdigest().upper()
    return payload


def fetch() -> list[dict]:
    body = json.dumps(signed_payload(), ensure_ascii=False, separators=(",", ":")).encode()
    request = Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "okhttp/4.12.0"},
    )
    context = ssl.create_default_context()
    with urlopen(request, timeout=30, context=context) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success"):
        raise RuntimeError(result.get("msg") or "Cangzhou API error")

    announcements = []
    for item in result.get("results", {}).get("announcementList", []):
        identity = f"{item.get('createDate', '')}\n{item.get('title', '')}"
        announcements.append(
            {
                "id": hashlib.sha1(identity.encode("utf-8")).hexdigest(),
                "date": item.get("createDate", ""),
                "title": item.get("title", ""),
                "type": "公告",
                "image": "",
                "description": item.get("content", ""),
                "url": "",
            }
        )
    return announcements


SOURCE = {"id": "cangzhou-bus", "name": "沧州行", "fetch": fetch}
