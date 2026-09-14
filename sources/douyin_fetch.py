"""Fetch public works from a Douyin profile using the resolver plugin's signer."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import httpx
import importlib.util

ABOGUS_PATH = Path(r"D:\AutomaticStart\AstrBotLauncher-0.2.0\AstrBot\data\plugins\astrbot_plugin_link_resolver\core\douyin\abogus.py")
spec = importlib.util.spec_from_file_location("resolver_abogus", ABOGUS_PATH)
abogus_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(abogus_module)
ABogus = abogus_module.ABogus
BrowserFingerprintGenerator = abogus_module.BrowserFingerprintGenerator

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 Edg/130.0.0.0"
TTWID = os.environ.get("DOUYIN_TTWID", "1%7Ch4Uu9_CL1Lxrju_ml8VsTociYL7i2g05bhZeHBk2LMI%7C1789090927%7Cd7fb7b96aec0b69c33e170faf0340af31c56ea25dc4f418be665b954b0520f6b")


async def fetch(sec_user_id: str) -> list[dict]:
    params = {
        "device_platform":"webapp", "aid":"6383", "channel":"channel_pc_web",
        "sec_user_id":sec_user_id, "max_cursor":"0", "count":"18",
        "publish_video_strategy_type":"2", "from_user_page":"1", "pc_client_type":"1",
        "version_code":"290100", "version_name":"29.1.0", "cookie_enabled":"true",
        "screen_width":"1920", "screen_height":"1080", "browser_language":"zh-CN",
        "browser_platform":"Win32", "browser_name":"Edge", "browser_version":"130.0.0",
        "browser_online":"true", "engine_name":"Blink", "engine_version":"130.0.0",
        "os_name":"Windows", "os_version":"10", "cpu_core_num":"12", "device_memory":"8",
        "platform":"PC", "downlink":"10", "effective_type":"4g", "round_trip_time":"50",
    }
    query = urlencode(params)
    fp = BrowserFingerprintGenerator.generate_fingerprint("Edge")
    bogus = ABogus(fp=fp, user_agent=UA).generate_abogus(query, "")[1]
    url = "https://www.douyin.com/aweme/v1/web/aweme/post/?" + query + "&a_bogus=" + bogus
    headers = {"User-Agent": UA, "Referer": "https://www.douyin.com/", "Cookie": f"ttwid={TTWID};"}
    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        response = await client.get(url)
    response.raise_for_status()
    payload = response.json()
    rows = payload.get("aweme_list") or payload.get("aweme_details") or []
    return [{"id": str(x.get("aweme_id") or x.get("item_id")), "date": datetime.fromtimestamp(int(x.get("create_time") or 0)).strftime("%Y-%m-%d %H:%M:%S") if x.get("create_time") else "",
             "title": x.get("desc") or "抖音公交公告", "type": "抖音公告",
             "description": x.get("desc") or "", "url": f"https://www.douyin.com/video/{x.get('aweme_id')}"}
            for x in rows if isinstance(x, dict) and (x.get("aweme_id") or x.get("item_id"))]


if __name__ == "__main__":
    print(json.dumps(asyncio.run(fetch(sys.argv[1])), ensure_ascii=False))
