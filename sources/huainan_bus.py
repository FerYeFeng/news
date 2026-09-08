"""Huainan Xing bus announcement source."""

from __future__ import annotations

import gzip
import json
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ENDPOINT = "https://hnnb.16bus.net/api/appClient/noAuth/publish/v1/getNoticeFromChannel"
BASE_URL = "https://hnnb.16bus.net"
HEADERS = {
    "osType": "1",
    "deviceType": "1",
    "versionName": "1.1.1.1",
    "versionCode": "30",
    "realLatitude": "0.0",
    "realLongitude": "0.0",
    "realCityCode": "0554",
    "deviceBrand": "Xiaomi",
    "systemVersion": "17",
    "channel": "1",
    "systemModel": "24129PN74C",
    "Authorization": " ",
    "deviceId": "e7101fb9a2044568a66f2f32007e3574",
    "cityCode": "340400",
    "appCode": "D0A960E40558E85E579596F214D21E193EA16375544207EC6FF74B0FBA0C55FB",
    "requestIds": "620aa1329e7dc46dea5438c81f9aa7e1",
    "adSource": "1",
    "stamp": "1788845288494",
    "digit": "25163",
    "Content-Type": "application/json; charset=UTF-8",
    "Accept-Encoding": "gzip",
    "User-Agent": "okhttp/4.12.0",
}


def fetch_page(page: int) -> tuple[str, list[dict]]:
    payload = json.dumps(
        {"channelCode": "RM21", "pageIndex": str(page)},
        separators=(",", ":"),
    ).encode("utf-8")
    request = Request(ENDPOINT, data=payload, method="POST", headers=HEADERS)
    with urlopen(request, timeout=30) as response:
        body = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            body = gzip.decompress(body)
    result = json.loads(body.decode("utf-8"))
    data = result.get("data")
    return str(result.get("code")), data if isinstance(data, list) else []


def fetch() -> list[dict]:
    announcements = []
    for page in range(1, 201):
        code, items = fetch_page(page)
        if code != "0" or not items:
            break
        for item in items:
            announcements.append(
                {
                    "id": item.get("id", ""),
                    "date": item.get("publishTime", ""),
                    "title": item.get("title", ""),
                    "type": "HTML",
                    "image": item.get("image", ""),
                    "description": item.get("subTitle", ""),
                    "url": urljoin(BASE_URL, str(item.get("url", ""))),
                }
            )
        if len(items) < 10:
            break
    return announcements


SOURCE = {
    "id": "huainan-bus",
    "name": "淮南行",
    "fetch": fetch,
}
