"""Announcement sources exposed by public bus mini-program APIs."""

from __future__ import annotations

import html
import json
import os
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USER_AGENT = "Mozilla/5.0 (Linux; Android 17; Mobile) MicroMessenger/8.0.76 MiniProgramEnv/android"


def plain_text(value: str | None) -> str:
    value = value or ""
    value = re.sub(r"<\s*br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</\s*(p|div|article|section|li)\s*>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"[ \t]+", " ", html.unescape(value)).strip()


def request_json(request: Request) -> dict:
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_nanchong() -> list[dict]:
    token = os.environ.get("GUOCHENG_X_ACCESS_TOKEN", "490106306183696384")
    headers = {
        "x-access-platform": "mp-weixin",
        "x-access-token": token,
        "Referer": "https://servicewechat.com/wxcf0989daedeea990/41/page-frame.html",
        "User-Agent": USER_AGENT,
    }
    result = request_json(Request("https://rt-api.steadan.com/appApi/system/notice/list", headers=headers))
    if result.get("code") != 200 or not isinstance(result.get("data"), list):
        raise RuntimeError(result.get("msg") or "果城行接口返回异常")
    return [
        {
            "id": str(item.get("noticeId", "")),
            "date": item.get("createTime", ""),
            "title": item.get("noticeTitle", ""),
            "type": "通知" if str(item.get("noticeType")) == "2" else "公告",
            "description": plain_text(item.get("noticeContent")),
            "url": "",
        }
        for item in result["data"]
    ]


def fetch_rikaze() -> list[dict]:
    query = urlencode({"number": 1, "pageSize": 100, "type": "GJXW"})
    endpoint = f"https://rkzapplet.tiamaes.com/usercenter/public/news/list?{query}"
    result = request_json(Request(endpoint, headers={"User-Agent": USER_AGENT}))
    rows = result.get("list")
    if not isinstance(rows, list):
        raise RuntimeError("日喀则公告接口返回异常")
    return [
        {
            "id": str(item.get("id", "")),
            "date": item.get("updateTime", ""),
            "title": item.get("title", ""),
            "type": "公交新闻",
            "description": item.get("simpleDesc", ""),
            "url": item.get("link", ""),
        }
        for item in rows
    ]


def fetch_hohhot() -> list[dict]:
    endpoint = "https://qcgjtx.hsgjgs.cn:1443/custom-server-qc/content/list"
    headers = {
        "channelId": "10000000",
        "Content-Type": "application/json",
        "sign": os.environ.get("HOHHOT_SIGN", "0a66a758fcdec2bfa0fee017a4ee2edb"),
        "timestamp": str(int(time.time() * 1000)),
        "uuid": os.environ.get("HOHHOT_UUID", "6Jk5S2iWjaCZ9WBltxFzdsdXDgjUjKxH"),
        "Referer": "https://servicewechat.com/wx87eaa968c7833e96/33/page-frame.html",
        "User-Agent": USER_AGENT,
    }
    items: list[dict] = []
    for page in (1, 2):
        body = json.dumps({"businessType": 11, "pageNum": page, "pageSize": 100}).encode("utf-8")
        result = request_json(Request(endpoint, data=body, method="POST", headers=headers))
        data = result.get("data") if isinstance(result, dict) else None
        rows = data.get("list") if isinstance(data, dict) else None
        if result.get("code") != 0 or not isinstance(rows, list):
            raise RuntimeError(result.get("message") or "呼和浩特公告接口返回异常")
        for item in rows:
            item_id = str(item.get("id", ""))
            items.append({
                "id": item_id,
                "date": item.get("addTime", ""),
                "title": item.get("title", ""),
                "type": "公交公告",
                "description": plain_text(item.get("content")),
                "url": "",
                "image": item.get("banner", ""),
            })
        if page >= int(data.get("totalPage") or 1):
            break
    return items


NANCHONG_SOURCE = {"id": "nanchong-bus", "fetch": fetch_nanchong, "allow_empty": True}
RIKAZE_SOURCE = {"id": "rikaze-bus", "fetch": fetch_rikaze, "allow_empty": True}
HOHHOT_SOURCE = {"id": "hohhot-miniapp", "fetch": fetch_hohhot, "allow_empty": True}
