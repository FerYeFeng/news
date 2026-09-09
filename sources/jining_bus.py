"""Jining Bus announcement source."""

from __future__ import annotations

import gzip
import json
from urllib.request import Request, urlopen


ENDPOINT = "https://miniqrcode.wuhanpe.com/AppServerWhpe/com/whpe/newsContent"
HEAD = (
    '{"appId":"03694610JNGJAPP","appVersion":"29",'
    '"cityCode":"03694610","cityQrParamVersion":"",'
    '"cmdType":"showNewsContentList","currentTime":"20260908102821",'
    '"deviceType":"Android","interfaceType":"","protocolVersion":"",'
    '"systemInfo":"","token":"","uid":""}'
)
DATA = (
    '{"pageChoose":"routeNoticePage","phoneNum":"",'
    '"spaceId":"17","startWord":""}'
)
SIGN = (
    "jG2Hp3SP03aIhyNlIfZ6/YCGGjtIzOBURXMx6tc55M9cahwoLTwEMaRxDBdO5VIl"
    "70QSCxDQxW4XDGt86Q3cNNHNIsYYoYEMNf8Q5lNlJfFB0E/zf3vOeKh7JPq0gyqV"
    "OFT05EMrnY583YsvsMKaTlbbbG2iuQL0VpS463It+cg="
)


def fetch() -> list[dict]:
    # currentTime is covered by the captured RSA signature; changing it alone invalidates sign.
    head = HEAD
    payload = json.dumps(
        {"head": head, "data": DATA, "sign": SIGN},
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.9.1",
        },
    )
    with urlopen(request, timeout=30) as response:
        body = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            body = gzip.decompress(body)
    result = json.loads(body.decode("utf-8"))
    if str(result.get("respCode")) != "01":
        raise RuntimeError(
            f"Jining API error {result.get('respCode')}: {result.get('respMsg')}"
        )

    announcements = []
    for item in result.get("data", {}).get("contentList", []):
        announcements.append(
            {
                "id": item.get("contentId", ""),
                "date": item.get("contentTime", ""),
                "title": item.get("contentName", ""),
                "type": item.get("contentType", ""),
                "image": item.get("contentImage", ""),
                "description": item.get("contentDesc", ""),
            }
        )
    return announcements


SOURCE = {
    "id": "jining-bus",
    "name": "济宁公交",
    "fetch": fetch,
}
