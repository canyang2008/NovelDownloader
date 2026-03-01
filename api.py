"""
小说下载 API 使用说明
=====================
端点: /download
支持方法: GET, POST

参数说明 (GET 使用查询字符串, POST 使用 JSON 体):
------------------------------------------------
url          : str  - 小说目录页 URL (必填)
orders       : str|list - 下载范围
count        : int  - 线程数，默认 1
title_key    : str  - 章节标题关键字起点，优先级小于 orders，默认 ""
mode         : int  - 下载模式: 0=浏览器, 1=API, 2=Requests，默认 0
delay        : list[float,float] - 下载延迟区间 [min, max]，默认 [3,5]
timeout      : int  - 超时时间(秒)，默认 10
max_retry    : int  - 最大重试次数，默认 3
interval     : int  - 重试间隔/退避因子，默认 2
user_data_dir: str  - Chrome 用户数据目录，默认 "data/Local/Default/User Data"
port         : int  - Chrome 调试端口，默认 9445
headless     : bool - 无头模式，默认 false
api_key      : str  - API 密钥，默认 ""
headers      : dict - 自定义 HTTP 头，默认 {}
cookie       : str  - Cookie 字符串，默认 ""
proxies      : dict - 代理，默认 {}

示例:
-----
GET:
  http://localhost:8900/download?url=http://example.com/novel&orders=1-5&mode=3

POST:
  curl -X POST -H "Content-Type: application/json" -d '{
    "url": "http://example.com/novel",
    "orders": "1-5,7",
    "mode": 3
  }' http://localhost:8900/download


Response
{
    "message":"massage",                            # str: 获取信息
    "data":{
        "url":"",                                   # str: 小说目录页
        "name":"",                                  # str: 小说名称
        "author":"",                                # str: 作者
        "author_description":"",                    # str: 作者自述
        "tags":[],                                  # list: 标签
        "last_update_chapter":"",                   # str: 最后更新章节
        "last_update_time":0000000000,              # int: 最后一次更新时间戳
        "cover_image_data":"",                      # str: 封面(Base64编码)
        "chapters":[                                # list: 章节所有信息
            {
                "title":"",                         # str: 章节标题
                "root":"",                          # str: 章节所属小说的url
                "url":"",                           # str: 章节url
                "order":1,                          # int: 章节位置
                "volume":"",                        # str: 章节所属卷
                "content":"",                       # str: 章节内容
                "timestamp":0000000000,             # int: 章节更新时间
                "count":0000,                       # int: 章节字数
                "is_complete":True,                 # bool: 获取的章节是否完整
                "images":[                          # list: 章节插图
                    [
                        "(1)",                      # str: 插图描述。有：f"(n) {描述}"，没有：(n)
                        ""                          # str: 章节数据(Base64编码)
                    ]
                ]
            }
        ]
    }
}
"""
import base64
from novel_downloader.models import DownloadMode
from novel_downloader.models.novel import Chapter, Novel
from flask import Flask, request, jsonify
from typing import Any, List, Dict, Optional
import json
from main import range_split
from novel_downloader.models.novel import img_to_json
from novel_downloader import parse_url, NovelDownloader

app = Flask(__name__)

def parse_bool(value: Any) -> bool:
    """将字符串或布尔值解析为布尔值。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def parse_params() -> Dict[str, Any]:
    """
    根据请求方法从不同来源提取参数，并转换类型。
    GET: 从 request.args 获取（均为字符串）
    POST: 从 request.get_json() 获取
    """
    if request.method == 'GET':
        args = request.args
        # 定义各字段的默认值和转换函数
        param_spec = {
            'url': (str, None),  # 必填，稍后单独检查
            'orders': (str, '1'),
            'count': (int, 1),
            'title_key': (str, ''),
            'mode': (int, 0),
            'delay': (json.loads, [3, 5]),  # 需要将 JSON 字符串解析为列表
            'timeout': (int, 10),
            'max_retry': (int, 3),
            'interval': (int, 2),
            'user_data_dir': (str, 'data/Local/Default/User Data'),
            'port': (int, 9445),
            'headless': (parse_bool, False),
            'api_key': (str, ''),
            'headers': (json.loads, {}),
            'cookies': (str, ''),
            'proxies': (json.loads, {})
        }
        params = {}
        for key, (converter, default) in param_spec.items():
            raw = args.get(key)
            if raw is None:
                params[key] = default
            else:
                try:
                    params[key] = converter(raw)
                except Exception as e:
                    raise ValueError(f"参数 {key} 格式错误: {e}")
        # 单独处理 url 必填
        if not params.get('url'):
            raise ValueError("缺少必填参数 'url'")
        return params
    else:  # POST
        data = request.get_json()
        if not data:
            raise ValueError("请求体必须为 JSON")
        url = data.get('url')
        if not url:
            raise ValueError("缺少必填字段 'url'")
        # 使用默认值填充缺失字段
        params = {
            'url': url,
            'orders': data.get('orders', 1),
            'title_key': data.get('title_key', ''),
            'count': data.get('count', 1),
            'mode': data.get('mode', 0),
            'delay': data.get('delay', [3, 5]),
            'timeout': data.get('timeout', 10),
            'max_retry': data.get('max_retry', 3),
            'interval': data.get('interval', 2),
            'user_data_dir': data.get('user_data_dir', 'data/Local/Default/User Data'),
            'port': data.get('port', 9445),
            'headless': data.get('headless', False),
            'api_key': data.get('api_key', ''),
            'headers': data.get('headers', {}),
            'cookies': data.get('cookies', ''),
            'proxies': data.get('proxies', {})
        }
        return params

def build_response_dict(
    total_downloaded_chapters: List[Optional[Chapter]],
    novel: Novel
) -> dict:
    """
    根据下载的章节列表和小说对象构建响应字典。
    """
    # 过滤掉 None 的章节
    valid_chapters = [ch for ch in total_downloaded_chapters if ch is not None]

    # 构建章节列表
    chapters_json = []
    for chapter in valid_chapters:
        # 处理图片：调用 img_to_json 得到元组列表，再转为列表列表
        images_raw = img_to_json(chapter.images)
        images_list = [list(img) for img in images_raw]

        chapter_dict = {
            "title": chapter.title,
            "root": novel.url,  # 章节所属小说的目录页 URL
            "url": chapter.url or "",
            "order": chapter.order,
            "volume": chapter.volume,
            "content": chapter.content,
            "timestamp": int(chapter.timestamp) if chapter.timestamp else 0,
            "count": chapter.count,
            "is_complete": chapter.is_complete,
            "images": images_list
        }
        chapters_json.append(chapter_dict)

    # 构建 data 部分
    data = {
        "url": novel.url,
        "name": novel.name,
        "author": novel.author or "",
        "author_description": novel.author_description or "",
        "tags": novel.tags,
        "last_update_chapter": novel.last_update_chapter or "",
        "last_update_time": int(novel.last_update_time) if novel.last_update_time else 0,
        "cover_image_data": base64.b64encode(novel.cover_image_data).decode() if novel.cover_image_data else "",
        "chapters": chapters_json
    }

    # 完整响应字典（message 可任意填写）
    response = {
        "message": "success",  # 可根据实际需求修改
        "data": data
    }
    return response

class ND(NovelDownloader):
    def __init__(self, config_option:int):
        super().__init__(config_option)

@app.route("/download", methods=["GET", "POST"])
def download():
    """
    处理下载请求
    """
    try:
        # 1. 解析参数
        params = parse_params()
        if params["mode"] == 0:
            mode = DownloadMode.BROWSER
        elif params["mode"] == 1:
            mode = DownloadMode.API
        elif params["mode"] == 2:
            mode = DownloadMode.REQUESTS
        else:
            mode = DownloadMode.BROWSER
        url, website = parse_url(params['url'])
        nd = ND(-1)
        nd.set(mode=mode,
               thread_count=params["count"],
               delay=params["delay"],
               timeout=params["timeout"],
               max_retry=params["max_retry"],
               interval=params["interval"],
               port=params["port"],
               headless=params["headless"],
               user_data_dir=params["user_data_dir"],
               api_key=params["api_key"],
               website=website,
               cookies=params['cookies'],
               proxies=params['proxies'],
               headers=params['headers'])
        novel = nd.get_info(url)
        if len(novel.chapters):
            max_order = len(novel.chapters)
        else:
            max_order = 25000
        orders = range_split(params['orders'], max_order)

        split_index = 0
        download_orders_list = []
        batch_size = nd.parser.batch_size
        while True:             # 分配任务
            download_orders_list.append(orders[split_index:split_index + batch_size])
            split_index += batch_size
            if split_index >= len(orders):break

        from concurrent.futures import ThreadPoolExecutor, as_completed
        total_downloaded_chapters:list[Chapter|None] = []
        with ThreadPoolExecutor(max_workers=params["count"]) as executor:
            # 创建任务列表
            tasks = []
            thread_index = -1
            for download_orders in download_orders_list:
                thread_index+=1
                index = thread_index % params["count"]
                tasks.append(executor.submit(
                    nd.get_chapters,
                    download_url=None,
                    orders=download_orders,
                    choice=index,
                ))
                if len(tasks) == nd.thread_count:
                    chapters_list:list[Chapter|None] = []
                    for future in as_completed(tasks):
                        chapters = future.result()
                        chapters_list.extend(chapters)
                    else:
                        if any(isinstance(item, Chapter) for item in chapters_list):
                            chapters_list.sort(key=lambda x:x.order)
                            total_downloaded_chapters.extend(chapters_list)
        response_data = build_response_dict(total_downloaded_chapters,novel)
        return jsonify(response_data)

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        return jsonify({"message": f"服务器内部错误: {e}"}), 500

if __name__ == "__main__":
    port = 8900
    app.run(debug=True, port=port)