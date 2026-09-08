"""Zibo bus latest announcement source."""

from __future__ import annotations

import html
import json
import re
import ssl
import time
import hashlib
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENDPOINT = "https://app.zbbus.com:8880/"
PAYLOAD = {
    "appId": "pd6f8vgbmlp5",
    "appVersion": "1.8.6",
    "cityCode": "zb",
    "datas": {"page": 1, "row": 10},
    "deviceBrand": "Xiaomi",
    "deviceId": "6ee751d7-442a-409e-a115-b9ae7c205103",
    "deviceModel": "24129PN74C",
    "from": 1,
    "lat": 0.0,
    "lng": 0.0,
    "reqType": "CommonInformationGain",
}


def signed_payload() -> dict:
    payload = {**PAYLOAD, "timestamp": int(time.time() * 1000)}
    canonical_parts = []
    for key, value in sorted(payload.items()):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        canonical_parts.append(f"{key}={value}")
    canonical = "&".join(canonical_parts)
    payload["sign"] = hashlib.md5(
        f"{canonical}&key=dalianyitongchuangxin".encode("utf-8")
    ).hexdigest().upper()
    return payload


def plain_text(value: str) -> str:
    value = re.sub(r"<\s*br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</\s*p\s*>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


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
        raise RuntimeError(result.get("msg") or "Zibo API error")

    return [
        {
            "id": str(item.get("id", "")),
            "date": item.get("sendDate", ""),
            "title": item.get("title", ""),
            "type": "最新10条（签名分页）",
            "image": item.get("imgUrl", ""),
            "description": plain_text(item.get("content", "")),
            "url": item.get("clientUrl", ""),
        }
        for item in result.get("results", {}).get("information", [])
    ]


SOURCE = {"id": "zibo-bus", "name": "淄博公交", "fetch": fetch}
