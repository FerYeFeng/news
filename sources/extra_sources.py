"""Additional bus announcement sources with small or signed result sets."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import ssl
from datetime import datetime
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


SSL_CONTEXT = ssl._create_unverified_context()


def text(value: str | None) -> str:
    value = value or ""
    value = re.sub(r"<\s*br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</\s*(p|article|section|div)\s*>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    return html.unescape(value).strip()


def stable_id(*parts: object) -> str:
    return hashlib.sha1("\n".join(map(str, parts)).encode("utf-8")).hexdigest()


def load_json(request: Request) -> dict:
    with urlopen(request, timeout=30, context=SSL_CONTEXT) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    request_headers = {"Content-Type": "application/json; charset=utf-8"}
    request_headers.update(headers or {})
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return load_json(Request(url, data=body, method="POST", headers=request_headers))


def post_form(url: str, payload: dict, headers: dict | None = None) -> dict:
    request_headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"}
    request_headers.update(headers or {})
    body = urlencode(payload).encode("utf-8")
    return load_json(Request(url, data=body, method="POST", headers=request_headers))


def panda_signed_payload(payload: dict) -> dict:
    """Build the Panda Bus request signature with a fresh timestamp."""
    payload = {**payload, "timestamp": int(datetime.now().timestamp() * 1000)}
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


def current_millis() -> str:
    return str(int(datetime.now().timestamp() * 1000))


def current_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def fetch_douyin_profile(profile_url: str) -> list[dict]:
    """Probe a Douyin profile; public server-side responses are often empty/blocked."""
    import subprocess
    from pathlib import Path
    import re
    venv = Path(r"D:\AutomaticStart\AstrBotLauncher-0.2.0\AstrBot\venv\Scripts\python.exe")
    script = Path(__file__).with_name("douyin_fetch.py")
    match = re.search(r"/user/([^/?]+)", profile_url)
    if not match:
        raise RuntimeError("无效的抖音账号地址")
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run([str(venv), str(script), match.group(1)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=45)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip()[-300:])
    import json
    rows = json.loads(result.stdout)
    if not rows:
        raise RuntimeError("抖音接口未返回作品")
    return rows


def fetch_heze() -> list[dict]:
    result = load_json(Request("http://weixin.hezebus.com:9008/hzapp/push/notificationNotice/notificationGeneral"))
    return [
        {"id": str(item["id"]), "date": item.get("releaseTime", ""), "title": item.get("title", ""),
         "type": item.get("name", "公告"), "image": item.get("showPictures", ""),
         "description": text(item.get("details")), "url": ""}
        for item in result.get("data", {}).get("notice", [])
    ]


def fetch_dezhou() -> list[dict]:
    base = "http://weixin.dzgj.cn:8081/LineServer/"
    result = load_json(Request(base + "docManage/DocManage!queryArticleList.action"))
    return [
        {"id": str(item["id"]), "date": item.get("createTime", ""), "title": item.get("name", ""),
         "type": item.get("moduleName", "公告"), "image": "", "description": "",
         "url": urljoin(base, item.get("relaPath", ""))}
        for item in result.get("articleList", [])
    ]


def fetch_weihai() -> list[dict]:
    signed_queries = (
        (5, "1789364847953", "kEybTtCl688IOygtMHttdGXWT6HWY%2BAGqoVIpF1iIXE%3D"),
        (4, "1789364847963", "0V1rNudzWbQtmpUMRQNYAOMtGiEuBZyxd32dq9HS0jY%3D"),
    )
    rows = []
    for type_code, timestamp, signature in signed_queries:
        url = (f"https://app.ibuscloud.com/v2/user/message/getUserMessage?typeCode={type_code}&page=1&count=10"
               "&uuid=00000000-499e-8d32-ffff-ffffef05ac4a&access_id=pt_wh_app"
               f"&timestamp={timestamp}&city=371000&token=&appSource=com.ibuscloud.weihaibus"
               f"&platform=Android&signature={signature}")
        result = load_json(Request(url, headers={"User-Agent": "okhttp/3.12.0"}))
        if str(result.get("result")) != "0" or not isinstance(result.get("items"), list):
            raise RuntimeError(result.get("message") or f"威海公交分类 {type_code} 接口返回失败")
        rows.extend(result["items"])
    items = {str(item.get("id")): item for item in rows}.values()
    return [
        {"id": str(item["id"]), "date": datetime.fromtimestamp(int(item["createTime"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
         "title": item.get("title", ""), "type": "威海公交公告", "image": "",
         "description": item.get("abstractInfo", ""), "url": item.get("h5", "")}
        for item in items
    ]


def fetch_longkou() -> list[dict]:
    result = post_form("http://www.lkgjt.xyz:7006/GetInfo/Notice", {"B": 1, "Len": 100, "Date": current_datetime()})
    return [
        {"id": stable_id(item.get("Date"), item.get("Title")), "date": item.get("Date", ""),
         "title": item.get("Title", ""), "type": "公告", "image": "",
         "description": item.get("Content", ""), "url": ""}
        for item in result.get("Data", [])
    ]


def fetch_baiyin() -> list[dict]:
    payload = {"clientType": "00", "data": {"newsType": "03", "pageNum": 1, "pageSize": 10},
               "machineType": "", "merchantId": "10000001", "phone": "",
               "sign": "CsWgIyzrwAHSuvp8Ll0DEJPu2bLm1bECn7Js8FGm7MWNjTHIqZdAwEFDFcnlfWOlNNiIjf8iQumH\n+/W2sWlNyOE5fufrMd5qbAzNtHg2T9pQV21lS7STWZBGXdB7v7+iSKZwJfivzoWApTG5zN6fc7YH\ne3GQ0S0b9edagGauCSk=\n",
               "timestamp": current_datetime(), "token": "", "userId": "", "version": "2.3.8"}
    result = post_json("https://www.bybus.com.cn:40001/tick/news-service/news/getAppNewsList", payload,
                       {"mode": "android", "version": "2.3.8"})
    return [
        {"id": item.get("newsId", ""), "date": item.get("publishTime", ""), "title": item.get("newsTitle", ""),
         "type": "最新10条（签名分页）", "image": item.get("iconUrl", ""),
         "description": item.get("newsBrif", ""), "url": ""}
        for item in result.get("data", [])
    ]


def fetch_xiongan() -> list[dict]:
    payload = {"clientType": "00", "data": {"newsType": "", "pageNum": 1, "pageSize": 10},
               "machineType": "", "merchantId": "10000001", "phone": "",
               "sign": "IksbeT6qkXIKIR9kbpQushmUSGuqEDqHxQ4gskSrF91rMBvEPKkM2en/5LQyw2i7RLYNJv3qjKqb\n5pXij+R0uMz+esuc4nF1Xs9EfaPNjpVBqmMg2VN9cs12TQ6ZfVOLWLteL8iq25pA1JFUN01S86X+\nF2EYFbzhtnprZxK7ZLI=\n",
               "timestamp": "2026-09-08 14:08:31", "token": "", "userId": "", "version": "3.16.4"}
    result = post_json("https://m.greenxax.com/tick/news-service/news/getAppNewsList", payload,
                       {"mode": "android", "version": "3.16.4"})
    return [
        {"id": item.get("newsId", ""), "date": item.get("publishTime", ""), "title": item.get("newsTitle", ""),
         "type": "最新10条（签名分页）", "image": item.get("iconUrl", ""),
         "description": item.get("newsBrif") or "", "url": ""}
        for item in result.get("data", [])
    ]


def fetch_xiangyang() -> list[dict]:
    payload = {"clientType": "00", "data": {"newsType": "01", "pageNum": 1, "pageSize": 10},
               "machineType": "", "merchantId": "10000001", "phone": "",
               "sign": "OWaIDuUTB6o2Jz+bHf9eECDddROMQRS8558EwAjDf1RY1aQ/0wEYTg3bYXDtEw9Qs/AAWPfZdtgn\nVJLmJwA5kbrBtpIvMRqc42M0MOmLnbZDyFtrxGeaRoaxz6NFKaMqkDu7dJmEa/oEWHQyPSqQDc15\nVyIzIOpfKCPIPXoGNn8=\n",
               "timestamp": "2026-09-08 14:20:36", "token": "", "userId": "", "version": "4.2.10"}
    result = post_json("https://xycx.xfbus.com.cn/tick/news-service/news/getAppNewsList", payload,
                       {"mode": "android", "version": "4.2.10", "User-Agent": "okhttp/3.14.9"})
    return [
        {"id": item.get("newsId", ""), "date": item.get("publishTime", ""),
         "title": item.get("newsTitle", ""), "type": "最新10条（签名分页）",
         "image": item.get("iconUrl", ""), "description": item.get("newsBrif") or "", "url": ""}
        for item in result.get("data", [])
    ]


def fetch_jitai() -> list[dict]:
    timer = current_millis()
    headers = {"deviceId": "123456", "timer": timer, "msgId": f"123456{timer}",
               "signature": "0430c440578adf2fca10e526ad511f44934038aab824481c2516af506c8143415503615767c994e657ccbe8259c3d15cd5ee1dd792f4d02171e21ca09a94be05954cd01cd39f501d9b4b1ef1d26c038d6f286bc503a1f7468bbc0ab6e3f9ee10276cfeef8bcd0164b35060e65f83b519cee92282fda58aacb0ad5bc35068dd17a297b46f5d6f1a"}
    result = post_form("http://123.135.128.171:7009/GetInfo/Notice",
                       {"B": 1, "Len": 100, "Date": current_datetime()}, headers)
    return [
        {"id": stable_id(item.get("Date"), item.get("Title")), "date": item.get("Date", ""),
         "title": item.get("Title", ""), "type": "公告", "image": "",
         "description": item.get("Content", ""), "url": ""}
        for item in result.get("Data", [])
    ]


def fetch_e_laiwu() -> list[dict]:
    timer = current_millis()
    headers = {"deviceId": "123456", "timer": timer, "msgId": f"123456{timer}",
               "signature": "04d4e217e9a32a9ec565f3daf7c6dfde16bd5e5a0623a23de97db17daaa3a61b5576b16338f9e3679b68359c9f1b66d7eb52d8acef0aeddfc5901e2fe1746d325e34d827f2c3ef5d675a03fcf766454c69b7ec9fc4cdb954ed5001d5fd0013598dcfbf81b752be9a6f4d4ddbcedf6342aab9eab9ac20171b25bc727dfe938ce9b40a64e8030fc7"}
    result = post_form("http://111.17.170.179:104/GetInfo/Notice",
                       {"B": 1, "Len": 100, "Date": current_datetime()}, headers)
    return [
        {"id": stable_id(item.get("Date"), item.get("Title")), "date": item.get("Date", ""),
         "title": item.get("Title", ""), "type": "最新100条（签名分页）", "image": "",
         "description": item.get("Content", ""), "url": ""}
        for item in result.get("Data", [])
    ]


def fetch_linyi() -> list[dict]:
    payload = panda_signed_payload({"appId": "pduksjr0qngp", "appVersion": "1.4.2", "cityCode": "linyi",
               "datas": {"page": 1, "row": 10, "tagId": 4}, "deviceBrand": "Xiaomi",
               "deviceId": "b8f965b5-7e71-43a7-9636-5841659472ab", "deviceModel": "24129PN74C",
               "from": 1, "lat": 0.0, "lng": 0.0, "reqType": "CommonInformationGain",
               })
    result = post_json("https://app.lygjgroup.com:8880/", payload, {"User-Agent": "okhttp/3.14.9"})
    return panda_information(result, "最新10条（签名分页）")


def fetch_notice_channel(endpoint: str, base_url: str, headers: dict, channel_code: str) -> list[dict]:
    announcements = []
    seen_ids = set()
    for page in range(1, 201):
        result = post_json(endpoint, {"channelCode": channel_code, "pageIndex": str(page)}, headers)
        items = result.get("data")
        if str(result.get("code")) != "0" or not isinstance(items, list) or not items:
            break
        new_items = [item for item in items if str(item.get("id", "")) not in seen_ids]
        if not new_items:
            break
        seen_ids.update(str(item.get("id", "")) for item in new_items)
        announcements.extend(
            {"id": str(item.get("id", "")), "date": item.get("publishTime", ""),
             "title": item.get("title", ""), "type": "公告", "image": item.get("image", ""),
             "description": item.get("subTitle", ""), "url": urljoin(base_url, item.get("url", ""))}
            for item in new_items
        )
        if len(items) < 10:
            break
    return announcements


def fetch_baoji() -> list[dict]:
    headers = {"osType": "1", "deviceType": "1", "versionName": "1.1.1.2", "versionCode": "32",
               "realCityCode": "0917", "deviceId": "e2d84e2b040d49899e27ecc871fd956c",
               "cityCode": "610300", "appCode": "D0A960E40558E85E579596F214D21E193EA16375544207EC6FF74B0FBA0C55FB",
               "requestIds": "9ed6c6e41fa0461893fe", "stamp": current_millis(), "digit": "39388",
               "User-Agent": "okhttp/4.8.0"}
    base = "https://app.baojigongjiao.com"
    return fetch_notice_channel(base + "/api/appClient/noAuth/publish/v1/getNoticeFromChannel", base, headers, "21")


def fetch_huaibei() -> list[dict]:
    headers = {"osType": "1", "deviceType": "1", "versionName": "1.0.3", "versionCode": "4",
               "realCityCode": "0319", "deviceId": "9d965901a9c24c57876034222b7b1a63",
               "cityCode": "340600", "appCode": "D0A960E40558E85E579596F214D21E193EA16375544207EC6FF74B0FBA0C55FB",
               "requestIds": "4a9d7b50022c7a65bdeb894de6b9253a", "stamp": current_millis(), "digit": "9072",
               "User-Agent": "okhttp/4.8.0"}
    base = "https://hbnb.huaibeigj.com"
    return fetch_notice_channel(base + "/api/appClient/noAuth/publish/v1/getNoticeFromChannel", base, headers, "RM21")


def fetch_wuhan() -> list[dict]:
    payload = {"xiaomaAppId": "A0CADFE6F3B914A2", "appKey": "A0CADFE6F3B914A2",
               "timeRequest": str(int(datetime.now().timestamp() * 1000)), "versionName": "1.2.1",
               "versionCode": "121", "phoneVersion": "17", "phoneModel": "24129PN74C",
               "phoneManufacturer": "Xiaomi", "deviceType": "1", "pushToken": "", "appType": 3,
               "codeType": 1, "cityCode": "420100", "channelId": "23000003", "code": "MODE43",
               "page": 1, "limit": 10}
    result = post_json("https://customized.wuhanbus.com/gateway/app/common/v2/user/getCommonMsgList", payload,
                       {"channelId": "23000003", "User-Agent": "okhttp/4.9.1"})
    return [
        {"id": str(item.get("id", "")),
         "date": datetime.fromtimestamp(int(item.get("createTime", 0)) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
         "title": item.get("title", ""), "type": "最新10条", "image": "", "description": "",
         "url": item.get("detailUrl", "")}
        for item in result.get("data", [])
    ]


def fetch_notification_general(url: str) -> list[dict]:
    result = load_json(Request(url))
    return [
        {"id": str(item.get("id", "")), "date": item.get("releaseTime", ""),
         "title": item.get("title", ""), "type": item.get("name", "通知"),
         "image": item.get("showPictures", ""), "description": text(item.get("details")), "url": ""}
        for item in result.get("data", {}).get("notice", [])
    ]


def fetch_rongcheng() -> list[dict]:
    return fetch_notification_general(
        "https://rcbus.org.cn:50013/rcapp/push/notificationNotice/notificationGeneral"
        f"?page=1&limit=1000&appLatestTimeStampStr={current_millis()}&signApp=sd3420b5fd0181b7fa1504c44eb8597786hy"
    )


def fetch_luoyang() -> list[dict]:
    result = load_json(Request("https://swkj.lybus.com/api/notice/findByType?noticeType=8"))
    return [
        {"id": str(item.get("id", "")), "date": item.get("createTime", ""),
         "title": item.get("title", ""), "type": "通告", "image": item.get("img", "") or "",
         "description": text(item.get("content")), "url": item.get("linkUrl", "") or ""}
        for item in result.get("rows", [])
    ]


def fetch_maanshan() -> list[dict]:
    return fetch_notification_general(
        "http://220.178.249.25:8081/masapp/push/notificationNotice/notificationGeneral"
    )


def fetch_raocheng() -> list[dict]:
    timestamp = current_millis()
    url = ("https://app.ibuscloud.com/v2/user/message/getUserMessage?typeCode=5&page=1&count=10"
           "&uuid=00000000-499e-8d32-ffff-ffffef05ac4a&access_id=pt_sr_app"
           f"&timestamp={timestamp}&city=361100&token=&appSource=com.ibuscloud.shangraobus"
           "&platform=Android&signature=ZgTLCB8sKZ7tnhNXMIeJJg%2B8E3CO49J2P%2BAwpUdakvo%3D")
    result = load_json(Request(url))
    if str(result.get("result")) != "0" or not isinstance(result.get("items"), list):
        raise RuntimeError(result.get("message") or "饶城通接口返回失败")
    return [
        {"id": str(item.get("id", "")),
         "date": datetime.fromtimestamp(int(item.get("createTime", 0)) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
         "title": item.get("title", ""), "type": "最新10条（签名分页）", "image": "",
         "description": item.get("abstractInfo", ""), "url": item.get("h5", "")}
        for item in result.get("items", [])
    ]


def fetch_longdu() -> list[dict]:
    result = post_form("https://h5.mygolbs.com/ApiData.do", {"CMD": 203, "CITYNAME": "濮阳市", "CITYKEY": "py001393"},
                       {"Origin": "https://h5.mygolbs.com", "Referer": "https://h5.mygolbs.com/?areacode=py001393"})
    return [
        {"id": stable_id(item.get("clickurl"), item.get("date"), item.get("title")), "date": item.get("date", ""),
         "title": item.get("title", ""), "type": item.get("type", "公告"), "image": item.get("imgurl", ""),
         "description": item.get("content", ""), "url": item.get("clickurl", "")}
        for item in result.get("data", [])
    ]


def fetch_binzhou() -> list[dict]:
    result = post_form("http://60.215.8.42:7006/GetInfo/Notice", {"B": 1, "Len": 2000, "Date": current_datetime()})
    return [
        {"id": stable_id(item.get("Date"), item.get("Title")), "date": item.get("Date", ""),
         "title": item.get("Title", ""), "type": "公告", "image": "",
         "description": item.get("Content", ""), "url": ""}
        for item in result.get("Data", [])
    ]


def fetch_tianjin() -> list[dict]:
    now = datetime.now()
    payload = {"version": "1.0.0", "cityCode": "3000", "appCode": "yt-bus",
               "actionId": now.strftime("%y-%m-%d_%H-%M-%S_") + f"_{now.microsecond // 1000:03d}null015下午", "data": {}}
    result = post_json("https://bus-slave.tjgjyt.com:18305/universal/user/v2/getNewsList", payload)
    return [
        {"id": str(item["id"]), "date": datetime.fromtimestamp(int(item["time"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"),
         "title": item.get("title", ""), "type": item.get("type", "公告"), "image": item.get("imageUrl", ""),
         "description": text(item.get("content")), "url": ""}
        for item in result.get("data", [])
    ]


def fetch_jilin() -> list[dict]:
    payload = panda_signed_payload({"appId": "pdmnwrqnrbyi", "appVersion": "1.2.6", "cityCode": "jilin",
               "datas": {"page": 1, "row": 10}, "deviceId": "fbf682e2-3fc4-432a-a127-389a51dcab77",
               "from": 1, "lat": 0.0, "lng": 0.0, "reqType": "CommonInformationGain",
               })
    result = post_json("https://shuttle.pandabus.cn:8802/", payload)
    return panda_information(result, "最新10条（签名分页）")


def fetch_quancheng() -> list[dict]:
    payload = panda_signed_payload({"appVersion": "1.0.0", "datas": '{"page":1,"row":10}', "deviceId": "123123123123123",
               "reqType": "CommonTravelInfo"})
    result = post_json("https://production.fengqiangwangluo.com:8880/", payload,
                       {"Origin": "https://h5.pandabus.cn", "Referer": "https://h5.pandabus.cn/"})
    items = result.get("results", {}).get("infoList", [])
    return [
        {"id": str(item.get("id", stable_id(item.get("createDate"), item.get("title")))),
         "date": item.get("createDate", ""), "title": item.get("title", ""),
         "type": "最新10条（签名分页）", "image": item.get("imgUrl", ""),
         "description": text(item.get("content")), "url": item.get("clientUrl", "")}
        for item in items
    ]


def panda_information(result: dict, type_name: str) -> list[dict]:
    return [
        {"id": str(item["id"]), "date": item.get("sendDate", item.get("createDate", "")),
         "title": item.get("title", ""), "type": type_name, "image": item.get("imgUrl", ""),
         "description": text(item.get("content")), "url": item.get("clientUrl", "")}
        for item in result.get("results", {}).get("information", [])
    ]


HEZE_SOURCE = {"id": "heze-bus", "name": "菏泽公交", "fetch": fetch_heze}
DEZHOU_SOURCE = {"id": "dezhou-bus", "name": "德州智能掌上公交", "fetch": fetch_dezhou}
WEIHAI_SOURCE = {"id": "weihai-bus", "name": "威海公交官方", "fetch": fetch_weihai}
LONGKOU_SOURCE = {"id": "longkou-bus", "name": "龙口掌上公交", "fetch": fetch_longkou}
BAIYIN_SOURCE = {"id": "baiyin-bus", "name": "白银公交", "fetch": fetch_baiyin}
XIONGAN_SOURCE = {"id": "xiongan-bus", "name": "雄安行", "fetch": fetch_xiongan}
XIANGYANG_SOURCE = {"id": "xiangyang-bus", "name": "襄阳出行", "fetch": fetch_xiangyang}
JITAI_SOURCE = {"id": "jitai-bus", "name": "公交e出行（济泰公交）", "fetch": fetch_jitai, "allow_empty": True}
E_LAIWU_SOURCE = {"id": "e-laiwu-bus", "name": "公交e出行（莱芜）", "fetch": fetch_e_laiwu}
LINYI_SOURCE = {"id": "linyi-bus", "name": "临沂公交", "fetch": fetch_linyi}
BAOJI_SOURCE = {"id": "baoji-bus", "name": "宝鸡行", "fetch": fetch_baoji}
WUHAN_SOURCE = {"id": "wuhan-bus", "name": "武汉公交", "fetch": fetch_wuhan}
HUAIBEI_SOURCE = {"id": "huaibei-bus", "name": "淮北智行", "fetch": fetch_huaibei}
RONGCHENG_SOURCE = {"id": "rongcheng-bus", "name": "荣成智能掌上公交", "fetch": fetch_rongcheng}
LUOYANG_SOURCE = {"id": "luoyang-bus", "name": "洛阳行", "fetch": fetch_luoyang}
MAANSHAN_SOURCE = {"id": "maanshan-bus", "name": "马鞍山掌上公交", "fetch": fetch_maanshan}
RAOCHENG_SOURCE = {"id": "raocheng-bus", "name": "绕城通", "fetch": fetch_raocheng}
LONGDU_SOURCE = {"id": "longdu-bus", "name": "龙都行（濮阳）", "fetch": fetch_longdu}
BINZHOU_SOURCE = {"id": "binzhou-bus", "name": "滨州交通", "fetch": fetch_binzhou}
TIANJIN_SOURCE = {"id": "tianjin-bus", "name": "天津交通", "fetch": fetch_tianjin}
JILIN_SOURCE = {"id": "jilin-bus", "name": "吉林行", "fetch": fetch_jilin}
QUANCHENG_SOURCE = {"id": "quancheng-bus", "name": "全澄通", "fetch": fetch_quancheng}
