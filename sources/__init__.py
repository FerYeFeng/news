"""Bus announcement registry in the user-defined city/platform order."""

from .anqing_bus import SOURCE as ANQING
from .cangzhou_bus import SOURCE as CANGZHOU
from .dongcheng_bus import SOURCE as DONGCHENG
from .extra_sources import (
    BAIYIN_SOURCE as BAIYIN,
    BAOJI_SOURCE as BAOJI,
    BINZHOU_SOURCE as BINZHOU,
    DEZHOU_SOURCE as DEZHOU,
    E_LAIWU_SOURCE as E_LAIWU,
    HEZE_SOURCE as HEZE,
    HUAIBEI_SOURCE as HUAIBEI,
    JILIN_SOURCE as JILIN,
    JITAI_SOURCE as JITAI,
    LINYI_SOURCE as LINYI,
    LONGDU_SOURCE as LONGDU,
    LONGKOU_SOURCE as LONGKOU,
    LUOYANG_SOURCE as LUOYANG,
    MAANSHAN_SOURCE as MAANSHAN,
    QUANCHENG_SOURCE as QUANCHENG,
    RAOCHENG_SOURCE as RAOCHENG,
    RONGCHENG_SOURCE as RONGCHENG,
    TIANJIN_SOURCE as TIANJIN,
    WEIHAI_SOURCE as WEIHAI,
    WUHAN_SOURCE as WUHAN,
    XIANGYANG_SOURCE as XIANGYANG,
    XIONGAN_SOURCE as XIONGAN,
)
from .extra_sources import fetch_douyin_profile
from .huainan_bus import SOURCE as HUAINAN
from .jinan_laiwu_bus import JINAN_SOURCE as JINAN, LAIWU_SOURCE as LAIWU
from .jining_bus import SOURCE as JINING
from .mygolbs_bus import SOURCES as MYGOLBS
from .taizhou_bus import SOURCE as TAIZHOU
from .yangzhou_bus import SOURCE as YANGZHOU
from .zibo_bus import SOURCE as ZIBO
from .weifang_bus import SOURCE as WEIFANG
from .mianyang_bus import SOURCE as MIANYANG
from .yinchuan_bus import SOURCE as YINCHUAN
from .longquan_bus import SOURCE as LONGQUAN
from .miniapp_sources import (
    HOHHOT_SOURCE as HOHHOT,
    NANCHONG_SOURCE as NANCHONG,
    RIKAZE_SOURCE as RIKAZE,
)


def configured(source: dict, city: str, platform: str) -> dict:
    return {**source, "city": city, "platform": platform, "name": f"{city} · {platform}"}


def missing(source_id: str, city: str, platform: str, homepage: str = "") -> dict:
    source = {
        "id": source_id,
        "city": city,
        "platform": platform,
        "name": f"{city} · {platform}",
        "fetch": lambda: [],
        "allow_empty": True,
        "unavailable": True,
    }
    if homepage:
        source["homepage"] = homepage
    return source


# Add source IDs here when you want the directory to show the yellow AI marker.
# Example: AI_SOURCE_IDS.add("jining-bus")
AI_SOURCE_IDS: set[str] = set()


# The h5.mygolbs entries already follow the first block of the requested table.
SOURCES = [
    {
        **source,
        "city": source["name"].removeprefix("掌上公交（").removesuffix("）"),
        "platform": "掌上公交",
        "name": f'{source["name"].removeprefix("掌上公交（").removesuffix("）")} · 掌上公交',
    }
    for source in MYGOLBS
]

SOURCES += [
    missing("toutiao-lanzhou", "兰州", "今日头条"),
    configured(JINING, "济宁", "济宁公交"),
    configured(JITAI, "济宁", "公交e出行"),
    configured(E_LAIWU, "莱芜", "公交e出行"),
    configured(TAIZHOU, "泰州", "泰州好出行"),
    configured(ANQING, "安庆", "安庆掌上公交"),
    configured(HUAINAN, "淮南", "淮南行"),
    configured(ZIBO, "淄博", "淄博出行"),
    configured(YANGZHOU, "扬州", "扬州掌上公交"),
    configured(MIANYANG, "绵阳", "绵阳公交集团官网"),
    configured(JINAN, "济南", "369出行"),
    configured(LAIWU, "莱芜", "369出行"),
    configured(YINCHUAN, "银川", "银川公交"),
    configured(CANGZHOU, "沧州", "沧州行"),
    configured(QUANCHENG, "江阴", "全澄通"),
    configured(LONGQUAN, "成都", "龙泉公交"),
    configured(JILIN, "吉林", "吉林行"),
    configured(TIANJIN, "天津", "天津公交"),
    configured(BINZHOU, "滨州", "滨州掌上公交"),
    configured(LONGDU, "濮阳", "龙都行"),
    configured(HEZE, "菏泽", "菏泽公交"),
    configured(BAIYIN, "白银", "白银公交"),
    configured(LONGKOU, "烟台", "龙口掌上公交"),
    configured(NANCHONG, "南充", "果城行微信小程序"),
    configured(RIKAZE, "日喀则", "微信小程序：日喀则公交"),
    configured(DEZHOU, "德州", "德州智能公交APP"),
    configured(WEIHAI, "威海", "威海公交APP"),
    configured(XIONGAN, "雄安新区", "雄安行App"),
    configured(RONGCHENG, "威海", "荣成智能掌上公交"),
    configured(LINYI, "临沂", "临沂公交APP"),
    configured(BAOJI, "宝鸡", "宝鸡行APP"),
    configured(WUHAN, "武汉", "武汉公交APP"),
    configured({"id": "gaoqing-douyin", "fetch": lambda: fetch_douyin_profile("https://www.douyin.com/user/MS4wLjABAAAAL8YyyVTt7NtUNHPvMrjN73PnK_XeGRBTTXuO75doeAr4EM5Llbqpt9q2HtVDdIT6"), "allow_empty": True}, "淄博", "抖音-高青公交（抖音号20059431886）"),
    configured({"id": "huguan-douyin", "fetch": lambda: fetch_douyin_profile("https://www.douyin.com/user/MS4wLjABAAAAFgKzIvc6axt25_Rvz_t3qczjfMIseLh5t99XRrSk7fE"), "allow_empty": True}, "壶关县", "抖音-壶关吉通安"),
    configured(LUOYANG, "洛阳", "洛阳行APP"),
    configured(WEIFANG, "潍坊", "潍坊公交app"),
    configured(HUAIBEI, "淮北", "淮北智行app"),
    configured(MAANSHAN, "马鞍山", "马鞍山掌上公交app"),
    missing("yibin-bus", "宜宾", "微信小程序：宜宾掌上公交"),
    missing("panan-bus", "磐安", "微信小程序：磐安畅行"),
    configured(DONGCHENG, "重庆", "东城公交app"),
    configured(RAOCHENG, "上饶", "饶城通"),
    configured(HOHHOT, "呼和浩特", "微信小程序：呼和浩特公交"),
    configured(XIANGYANG, "襄阳", "襄阳出行"),
    configured({"id": "xuzhou-douyin", "fetch": lambda: fetch_douyin_profile("https://www.douyin.com/user/MS4wLjABAAAA7q6zIkY7843XFkn0nDqC0iU86o9S2M7lB8tS49z0eyQ"), "allow_empty": True}, "徐州", "抖音-徐萧徐宿城际公交（抖音号24514231693）"),
]
