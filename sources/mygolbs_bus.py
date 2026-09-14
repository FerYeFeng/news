"""City announcement sources served by h5.mygolbs.com."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import html
import json
import re
from html.parser import HTMLParser
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENDPOINT = "https://h5.mygolbs.com/ApiData.do"
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://h5.mygolbs.com",
    "Referer": "https://h5.mygolbs.com/",
    "User-Agent": "Mozilla/5.0 bus-news-aggregator/1.0",
    "X-Requested-With": "XMLHttpRequest",
}
DETAIL_EXECUTOR = ThreadPoolExecutor(max_workers=1)

AREAS = [
    ("tianjin", "天津", "天津市"),
    ("nanjing", "南京", "南京市"),
    ("nanchang", "南昌", "南昌市"),
    ("xuzhou", "徐州", "徐州市"),
    ("lanzhou", "兰州", "兰州市"),
    ("shijiazhuang", "石家庄", "石家庄市"),
    ("haikou", "海口", "海口市"),
    ("liuzhou", "柳州", "柳州市"),
    ("zhenjiang", "镇江", "镇江市"),
    ("jiujiang", "九江", "九江市"),
    ("yueyang", "岳阳", "岳阳市"),
    ("neijiang", "内江", "内江市"),
    ("luzhou", "泸州", "泸州市"),
    ("mengzi", "蒙自", "蒙自市"),
    ("heze", "菏泽", "菏泽市"),
    ("wenzhou", "温州", "温州市"),
    ("baoding", "保定", "保定市"),
    ("nanning", "南宁", "南宁市"),
    ("hohhot", "呼和浩特", "呼和浩特市"),
    ("yinchuan", "银川", "银川市"),
    ("jian", "吉安", "吉安市"),
    ("binhai", "盐城滨海", "盐城市滨海县"),
    ("funing", "盐城阜宁", "阜宁县"),
    ("linyi", "临沂", "临沂市"),
    ("guiyang", "贵阳", "贵阳市"),
    ("jiangmen", "江门", "江门市"),
    ("jingdezhen", "景德镇", "景德镇市"),
    ("suizhou", "随州", "随州市"),
    ("fuzhou-jx", "抚州", "抚州市"),
    ("puyang", "濮阳", "濮阳市"),
    ("qingdao", "青岛", "青岛市"),
    ("shangrao", "上饶", "上饶市"),
    ("zhangye", "张掖", "张掖市"),
]


def normalize_url(value: str | None) -> str:
    return (value or "").replace(
        "http://quanguo.mygolbs.com:8081/MyBusServer",
        "https://quanguo.mygolbs.com/MyBusServer",
    )


class DetailTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.parts.append(value)


def fetch_detail(url: str) -> tuple[str, str]:
    if not url:
        return "", ""
    request = Request(url, headers={"User-Agent": HEADERS["User-Agent"]})
    with urlopen(request, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
    parser = DetailTextParser()
    parser.feed(body)
    detail_text = html.unescape("\n".join(parser.parts))
    match = re.search(r"发布时间\s*[:：]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)", detail_text)
    published_at = match.group(1) if match else ""
    description = re.sub(r"^.*?发布时间\s*[:：]\s*[^\n]+\n?", "", detail_text, count=1, flags=re.S).strip()
    return published_at, description


def safe_fetch_detail(url: str) -> tuple[str, str]:
    try:
        return fetch_detail(url)
    except Exception:
        return "", ""


def fetch_city(city_name: str) -> list[dict]:
    body = urlencode({"CMD": "203", "CITYNAME": city_name, "CITYKEY": ""}).encode("utf-8")
    request = Request(ENDPOINT, data=body, method="POST", headers=HEADERS)
    with urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))
    if result.get("status") != 1:
        raise RuntimeError(result.get("msg") or result.get("message") or "掌上公交接口返回失败")

    rows = result.get("data") or []
    urls = [normalize_url(item.get("clickurl")) for item in rows]
    details = list(DETAIL_EXECUTOR.map(safe_fetch_detail, urls))

    announcements = []
    for item, url, (published_at, description) in zip(rows, urls, details):
        identity = "\n".join((city_name, str(item.get("date", "")), str(item.get("title", ""))))
        announcements.append(
            {
                "id": hashlib.sha1(identity.encode("utf-8")).hexdigest(),
                "date": published_at or item.get("date", ""),
                "title": item.get("title", ""),
                "type": item.get("type", "公告"),
                "image": "",
                "description": description,
                "url": url,
            }
        )
    return announcements


def make_source(source_id: str, label: str, city_name: str) -> dict:
    return {
        "id": f"mygolbs-{source_id}",
        "name": f"掌上公交（{label}）",
        "fetch": lambda city_name=city_name: fetch_city(city_name),
        "allow_empty": True,
    }


SOURCES = [make_source(*area) for area in AREAS]
