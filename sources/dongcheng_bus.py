"""Dongcheng Bus announcements via the Panda Bus API."""

from __future__ import annotations

import hashlib
import html
import json
import re
import ssl
import time
from urllib.request import Request, urlopen


ENDPOINT = "https://dcbus.cqdcgj.com:8880/"
BASE_PAYLOAD = {
    "appId": "pdbvmuujva0t",
    "appVersion": "1.3.5",
    "cityCode": "cqdc",
    "deviceBrand": "Xiaomi",
    "deviceId": "dd1b55eb-0d32-4cb5-80b3-830fdcb03d4e",
    "deviceModel": "24129PN74C",
    "from": 1,
    "lat": 0.0,
    "lng": 0.0,
    "reqType": "CommonService",
}


def _signed_payload() -> dict:
    payload = {**BASE_PAYLOAD, "timestamp": int(time.time() * 1000)}
    parts = []
    for key, value in sorted(payload.items()):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        parts.append(f"{key}={value}")
    canonical = "&".join(parts)
    payload["sign"] = hashlib.md5(
        f"{canonical}&key=dalianyitongchuangxin".encode("utf-8")
    ).hexdigest().upper()
    return payload


def _text(value: object) -> str:
    value = re.sub(r"<\s*br\s*/?>", "\n", str(value or ""), flags=re.I)
    value = re.sub(r"</\s*p\s*>", "\n", value, flags=re.I)
    return html.unescape(re.sub(r"<[^>]+>", "", value)).strip()


def fetch() -> list[dict]:
    body = json.dumps(
        _signed_payload(), ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "okhttp/3.12.1",
        },
    )
    with urlopen(request, timeout=30, context=ssl.create_default_context()) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not result.get("success"):
        raise RuntimeError(result.get("msg") or "东城公交接口返回失败")

    rows = (result.get("results") or {}).get("announcementList") or []
    announcements = []
    for item in rows:
        content = _text(item.get("content"))
        title = _text(item.get("title")) or (content.splitlines()[0].strip() if content else "公交公告")
        identity = f"{item.get('createDate', '')}\n{title}"
        announcements.append({
            "id": hashlib.sha1(identity.encode("utf-8")).hexdigest(),
            "date": item.get("createDate") or "",
            "title": title,
            "type": "东城公交公告",
            "image": "",
            "description": content,
            "url": "",
        })
    return announcements


SOURCE = {"id": "dongcheng-bus", "name": "东城公交", "fetch": fetch}
