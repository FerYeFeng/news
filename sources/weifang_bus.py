"""Weifang Tong (潍坊公交) announcements."""
from __future__ import annotations
import base64, html, json, ssl, time
from urllib.request import Request, urlopen

ENDPOINT = "https://mobile.wfsmk.cn:3000/appops/appopsPageNews/queryNews/V1"
# The app signs these fields internally. Keeping the latest captured envelope allows
# the endpoint to be probed and supports servers configured to return plain JSON.
CAPTURED = {
    "joininstid": "12564211", "joininstssn": "202609081413403390638",
    "reqtime": "141340",
    "dataenc": "dYOBqf3tJugheNdJQV+hl8GMXnopf0wI43sYN1D/LnpxdTA+0XizVzfXmklGIFRngfM3A1QVljcn7GNA04jYlQ==",
    "hdataenc": "q5GJTtyh47W0WO4FSBCXm/1TzffdLL6sCBYKWgZo76e4bphLQEralMyQKOFwtXHmtMxVsSjc6ky1DGtWs1i+2A==",
    "sign": "cPxjI/nIBWmOaScQ0rHRonX1G+34o2GW5JVz2JX+juc9PXOsW8Owx6oDPfBR6CG0Hwr5zkF1KzcnYKkWQtvk7A==",
    "reqdate": "20260908",
}

def _plain(v):
    return html.unescape(str(v or "")).replace("<br>", "\n").strip()

def fetch() -> list[dict]:
    payload = dict(CAPTURED)
    payload["reqdate"] = time.strftime("%Y%m%d")
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
    req = Request(ENDPOINT, data=body, method="POST", headers={"Content-Type":"application/json; charset=UTF-8", "User-Agent":"okhttp/4.9.3", "Accept-Encoding":"gzip"})
    with urlopen(req, timeout=30, context=ssl.create_default_context()) as r:
        obj = json.loads(r.read().decode("utf-8"))
    data = obj.get("data")
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("list") or data.get("rows") or data.get("newsList") or []
    else:
        rows = []
    if not rows:
        raise RuntimeError("接口返回加密公告或暂无数据，需应用动态签名解密")
    out=[]
    for i,x in enumerate(rows):
        out.append({"id":str(x.get("id") or x.get("newsId") or i), "date":x.get("date") or x.get("publishTime") or x.get("createTime") or "", "title":x.get("title") or x.get("newsTitle") or "", "type":"潍坊公交公告", "description":_plain(x.get("content") or x.get("remark")), "url":x.get("url") or x.get("link") or ""})
    return out

SOURCE = {"id":"weifang-bus", "name":"潍坊公交", "fetch":fetch}
