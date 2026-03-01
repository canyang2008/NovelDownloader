import re

from novel_downloader.models import Website


def parse_url(url:str) -> tuple[str,Website]:
    """解析并格式化url"""
    if 'https://changdunovel.com' in url:  # 处理番茄小说的分享链接
        book_id = re.search(r"book_id=(\d+)", url).group(1)
        url = 'https://fanqienovel.com/page/' + book_id
        return url, Website.FANQIE
    if "https://magev6.if.qidian.com/h5/share" in url:  # 处理起点小说的分享链接
        book_id = re.search(r"bookId=(\d+)", url).group(1)
        url = 'https://www.qidian.com/book/' + book_id
        return url, Website.QIDIAN

    url = url.split("?")[0].strip()
    if 'https://fanqienovel.com' in url:
        return url, Website.FANQIE
    elif 'https://www.qidian.com' in url:
        return url, Website.QIDIAN
    elif "https://www.biqugequ.org" in url:
        url = url.replace(".html","")
        return url, Website.BIQUGE
    else:
        return url, Website.OTHER

class FeatureNotSupportedError(Exception):
    def __init__(self,msg: str) -> None:
        self.msg = msg
    def __str__(self) -> str:
        return self.msg
class APIError(Exception):
    def __init__(self, provider:str,msg: str) -> None:
        self.provider = provider
        self.msg = msg
    def __str__(self) -> str:
        return self.msg