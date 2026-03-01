enable=True
import re
import time
from typing import Any
from novel_downloader.models import DownloadMode
from novel_downloader.models.novel import *
from novel_downloader.parsers import FeatureNotSupportedError
from novel_downloader.parsers.base import BaseParser
from bs4 import BeautifulSoup

from novel_downloader.core.downloader import ChromeDownloader, APIDownloader, RequestsDownloader

def user_status(html):
    soup = BeautifulSoup(html, 'lxml')
    # 右上角登录界面
    user_info_div = soup.find("div", class_="nri")
    if user_info_div is None:
        user_state_code = -1
    else:
        user_state_code = 1
    return user_state_code

class _BiqugeForHtml(BaseParser):

    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.next_page_url = None
        self.batch_size = 1
        self.PAGED = True

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str, Any]] | None:
        pass
    def parse_novel_info(self, content, **kwargs) -> Novel:

        url = kwargs.get("url")
        label = []
        last_update_for_chapter, last_update_for_time = None, None
        soup = BeautifulSoup(content, 'html.parser')
        info_data = soup.find("div", id="info")  # 信息
        name = info_data.find("h1").get_text()
        p_list = info_data.find_all("p")
        author = ""
        for p in p_list:
            if p.text.startswith("作  者："):
                author = p.find("a").get_text()
            if p.text.startswith("分  类："):
                label = [p.find("a").get_text()]
            if p.text.startswith("最后更新："):
                last_update_for_time = time.mktime(time.strptime(p.text[5:], "%Y-%m-%d %H:%M:%S"))
            if p.text.startswith("最新更新："):
                last_update_for_chapter = p.get_text()
        book_cover_url = soup.find("div", id="fmimg").find("img").get("src")
        book_cover_data = ''  # base64.b64encode(requests.get(book_cover_url).content).decode("utf-8") # 访问会卡在这里
        web_chapter_list = soup.find('div', id='list').find_all('dd')
        abstract = soup.find("div", id="intro").get_text()
        novel = Novel(
            url=url,
            name=name,
            author=author,
            tags=label,
            description=abstract,
            last_update_chapter=last_update_for_chapter,
            last_update_time=last_update_for_time,
        )
        # 更新下载列表
        all_title_list = [title.find("a").get("title") for title in web_chapter_list]
        all_url_list = ["https://www.biqugequ.org/" + url.find("a").get("href") for url in web_chapter_list]
        order = 1
        for title, chapter_url in zip(all_title_list, all_url_list):
            chapter = Chapter(
                title=title,
                url=chapter_url,
              order=order
            )
            order += 1
            novel.update(chapter)
        return novel

    def parse_chapter_content(self, content, orders, **kwargs) ->tuple[dict, str | None]:
        # 笔趣阁，一章分页设计
        soup = BeautifulSoup(content, 'lxml')
        novel_content_div = soup.find('div', id='content').find_all("p")
        next_url = soup.find("div", class_="bottem2").find("a", id="pager_next").get("href")
        # 当下一页是当前章节的下一分页时
        if re.search(rf"_\d.html", next_url):
            next_url = "https://www.biqugequ.org" + next_url
            novel_content_div = novel_content_div[:-1]
        else:
            next_url = None
        for p in novel_content_div:
            kwargs['text'] += p.get_text() + '\n'
        return kwargs, next_url


class BiqugeForBrowser(_BiqugeForHtml):
    def __init__(self,downloader:ChromeDownloader,**kwargs):
        super().__init__(**kwargs)
        self.user_status:int = -1
        self.novel = None
        self.PAGED = True
        self.downloader = downloader

    def parse_novel_info(self, content, **kwargs) -> Novel:
        html = self.downloader.get(url=content)
        self.user_status = user_status(html)
        return super().parse_novel_info(content=html,url = content,**kwargs)

    def parse_chapter_content(self, content, orders, **kwargs) -> tuple[Chapter | None]:
        html = self.downloader.get(url=content)
        if 'text' not in kwargs.keys():
            kwargs['text'] = ""
        kwargs,next_url= super().parse_chapter_content(content=html, orders=orders, **kwargs)
        if next_url is None:
            chapter = self.novel[orders[0]]
            chapter.content = kwargs['text']
            chapter.is_complete = True
            return (chapter,)
        else:return self.parse_chapter_content(content=next_url,orders=orders ,**kwargs)


class BiqugeForReq(_BiqugeForHtml):
    def __init__(self, downloader:RequestsDownloader,**kwargs):
        super().__init__(**kwargs)
        self.novel = None
        self.downloader = downloader

    def parse_novel_info(self, content, **kwargs) -> Novel:
        html = self.downloader.get(url=content)
        self.novel = super().parse_novel_info(content=html,url = content, **kwargs)
        return self.novel
    def parse_chapter_content(self, content, orders, **kwargs) ->tuple[Chapter|None]:
        html = self.downloader.get(url=content,**kwargs)
        if 'text' not in kwargs.keys():
            kwargs['text'] = ""
        kwargs,next_url= super().parse_chapter_content(content=html, orders=orders, **kwargs)
        if next_url is None:
            chapter = self.novel[orders[0]]
            chapter.content = kwargs['text']
            chapter.is_complete = True
            return (chapter,)
        else:return self.parse_chapter_content(content=next_url,orders=orders ,**kwargs)

class BiqugeParser(BaseParser):
    def __init__(self,downloader:ChromeDownloader|APIDownloader|RequestsDownloader, **kwargs):
        super().__init__(**kwargs)
        if downloader.MODE == DownloadMode.BROWSER:
            self.__parser = BiqugeForBrowser(downloader=downloader,**kwargs)
        elif downloader.MODE == DownloadMode.API:
            raise FeatureNotSupportedError("biqugequ暂不支持API")
        elif downloader.MODE == DownloadMode.REQUESTS:
            self.__parser = BiqugeForReq(downloader=downloader,**kwargs)
        self.batch_size = self.__parser.batch_size
        self.__parser.downloader = downloader

    def update(self,novel:Novel = None,downloader:ChromeDownloader|APIDownloader|RequestsDownloader = None,**kwargs):
        if novel:
            self.novel = novel
            self.__parser.novel = novel
        if downloader:
            self.__parser.downloader = downloader

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> str:
        raise FeatureNotSupportedError("biqugequ不支持搜索功能")
    def parse_novel_info(self, content, **kwargs) -> Novel:
        return self.__parser.parse_novel_info(content=content, **kwargs)
    def parse_chapter_content(self, content, orders, **kwargs: list) -> tuple[Chapter | None]:
        download_url = self.novel[orders[0]].url
        kwargs["url"] = download_url
        return self.__parser.parse_chapter_content(content=download_url, orders=orders,**kwargs)