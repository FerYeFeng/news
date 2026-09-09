# 公交公告汇总

双击 `start.bat`（或 `更新并查看公告.bat`）启动服务。服务监听 `0.0.0.0:9092`，浏览器访问 <http://127.0.0.1:9092/>。程序每 3 分钟更新全部来源一次，HTML 每页最多 30 条，公告数据保存在 `html/*.json`。

## 接口清单

| 平台 | 方法 | 接口 | 备注 |
|---|---|---|---|
| 掌上公交（33 个城市站点） | POST | `https://h5.mygolbs.com/ApiData.do` | 表单 `CMD=203`、`CITYNAME`、`CITYKEY`；时间动态生成 |
| 济宁公交 | POST | `https://miniqrcode.wuhanpe.com/AppServerWhpe/com/whpe/newsContent` | `showNewsContentList`；`head` 与 RSA 签名绑定 |
| 淮南行 | POST | `https://hnnb.16bus.net/api/appClient/noAuth/publish/v1/getNoticeFromChannel` | `channelCode=RM21`；分页；`stamp` 动态生成 |
| 泰州好出行 | GET | `https://taizhou.nandasoft-its.com:8887/tzhcx/notice/toList?type=1` | HTML 列表解析 |
| 安庆掌上公交 | GET | `http://223.247.144.152:3003/app-services/notice/public/listAllClass?timestamp=...` | 时间戳动态生成 |
| 扬州掌上公交 | GET | `http://61.132.33.218:85/prod-api/infomanage/app/client/routesDynamic/list` | `routeName`、`pageNum`、`pageSize` |
| 济南/莱芜 369 出行 | GET | `https://api.369cx.cn/v2/Notice/GetNoticeList/{page}` | 自动分页，按类型区分城市 |
| 沧州行 | POST | `https://app.cangzhoubus.com:8880/` | `CommonService`；MD5 签名密钥 `dalianyitongchuangxin` |
| 淄博出行 | POST | `https://app.zbbus.com:8880/` | `CommonInformationGain`；MD5 签名密钥 `dalianyitongchuangxin` |
| 菏泽公交 | GET | `http://weixin.hezebus.com:9008/hzapp/push/notificationNotice/notificationGeneral` | 公告 JSON |
| 德州智能掌上公交 | GET | `http://weixin.dzgj.cn:8081/LineServer/docManage/DocManage!queryArticleList.action` | 文章列表 JSON |
| 威海公交官方 | GET | `https://app.ibuscloud.com/v2/user/message/getUserMessage` | `typeCode=5`；需要 ibuscloud 动态签名 |
| 龙口掌上公交 | POST | `http://www.lkgjt.xyz:7006/GetInfo/Notice` | 表单 `B`、`Len`、`Date` |
| 白银公交 | POST | `https://www.bybus.com.cn:40001/tick/news-service/news/getAppNewsList` | `newsType=03`；签名样本 |
| 雄安行 | POST | `https://m.greenxax.com/tick/news-service/news/getAppNewsList` | 签名与抓包时间绑定 |
| 公交 e 出行（济泰/莱芜） | POST | `http://123.135.128.171:7009/GetInfo/Notice` / `http://111.17.170.179:104/GetInfo/Notice` | 表单公告接口；签名请求头 |
| 临沂公交 APP | POST | `https://app.lygjgroup.com:8880/` | `CommonInformationGain`；MD5 签名密钥 `dalianyitongchuangxin` |
| 宝鸡行 | POST | `https://app.baojigongjiao.com/api/appClient/noAuth/publish/v1/getNoticeFromChannel` | `channelCode=21`；分页 |
| 武汉公交 APP | POST | `https://customized.wuhanbus.com/gateway/app/common/v2/user/getCommonMsgList` | `channelId=23000003` |
| 淮北智行 APP | POST | `https://hbnb.huaibeigj.com/api/appClient/noAuth/publish/v1/getNoticeFromChannel` | `channelCode=RM21`；分页 |
| 荣成智能掌上公交 | GET | `https://rcbus.org.cn:50013/rcapp/push/notificationNotice/notificationGeneral` | `page`、`limit`、`appLatestTimeStampStr` |
| 洛阳行 APP | GET | `https://swkj.lybus.com/api/notice/findByType?noticeType=8` | `noticeType=8` |
| 马鞍山掌上公交 APP | GET | `http://220.178.249.25:8081/masapp/push/notificationNotice/notificationGeneral` | 公告 JSON |
| 饶城通 | GET | `https://app.ibuscloud.com/v2/user/message/getUserMessage` | `access_id=pt_sr_app`；需要 ibuscloud 动态签名 |
| 龙都行（濮阳） | POST | `https://h5.mygolbs.com/ApiData.do` | `CMD=203`、`CITYKEY=py001393` |
| 滨州交通 | POST | `http://60.215.8.42:7006/GetInfo/Notice` | 表单 `B`、`Len`、`Date` |
| 天津交通 | POST | `https://bus-slave.tjgjyt.com:18305/universal/user/v2/getNewsList` | `actionId` 动态生成 |
| 吉林行 | POST | `https://shuttle.pandabus.cn:8802/` | MD5 签名密钥 `dalianyitongchuangxin` |
| 江阴 · 全澄通 | POST | `https://production.fengqiangwangluo.com:8880/` | `CommonTravelInfo`；MD5 签名密钥 `dalianyitongchuangxin` |
| 东城公交 APP | POST | `https://dcbus.cqdcgj.com:8880/` | `CommonService`；MD5 签名密钥 `dalianyitongchuangxin` |
| 襄阳出行 | POST | `https://xycx.xfbus.com.cn/tick/news-service/news/getAppNewsList` | `newsType=01`；签名与抓包时间绑定 |
| 潍坊公交 APP | POST | `https://mobile.wfsmk.cn:3000/appops/appopsPageNews/queryNews/V1` | `dataenc/hdataenc` 加密，需要 APK 动态密钥 |

掌上公交 33 个城市站点分别为：天津、南京、南昌、徐州、兰州、石家庄、海口、柳州、镇江、九江、岳阳、内江、泸州、蒙自、菏泽、温州、保定、南宁、呼和浩特、银川、吉安、盐城滨海、盐城阜宁、临沂、贵阳、江门、景德镇、随州、抚州、濮阳、青岛、上饶、张掖。它们共用 `h5.mygolbs.com/ApiData.do`，通过 `CITYNAME` 区分站点。

## 尚未录入接口

以下平台目前只保留页面目录位置，没有可用公告接口，页面显示紫色：

- 兰州 · 今日头条
- 绵阳 · 绵州通
- 银川 · 银川行
- 成都 · 龙泉公交
- 南充 · 果城行微信小程序
- 日喀则 · 日喀则公交微信小程序
- 淄博 · 抖音-高青公交
- 壶关县 · 抖音-壶关吉通安
- 宜宾 · 宜宾掌上公交微信小程序
- 磐安 · 磐安畅行微信小程序
- 呼和浩特 · 呼和浩特公交微信小程序
- 徐州 · 抖音-徐萧徐宿城际公交

## 状态颜色

- 深绿色：今天有公告。
- 浅绿色：昨天有公告。
- 红色：接口请求失败、签名失败、超时或服务端错误。
- 粉色：请求成功但公告内容为空；有缓存时仍展示历史公告。
- 紫色：尚未录入抓取接口。
- 黄色：用户手动设置的 AI 标记。

## 添加来源

在 `sources` 目录新增模块，提供包含 `id`、`name`、`fetch` 的 `SOURCE` 字典。`fetch` 返回字段统一为 `id`、`date`、`title`、`type`、`image`、`description`、`url`，然后在 `sources/__init__.py` 注册。
