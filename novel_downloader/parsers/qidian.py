enable=True
import json
import re
import time
from typing import Any
import requests
from novel_downloader.core.downloader import ChromeDownloader, APIDownloader, RequestsDownloader
from novel_downloader.models import DownloadMode
from novel_downloader.models.novel import *
from novel_downloader.parsers import FeatureNotSupportedError
from novel_downloader.parsers.base import BaseParser
from bs4 import BeautifulSoup, Tag


def user_status(html):
    soup = BeautifulSoup(html, 'lxml')
    user_info_div = soup.find("div", class_="ml-auto text-s-gray-900 text-bo2 relative group")
    if user_info_div:
        if user_info_div.find('Button'):
            user_state_code = 0
        else:user_state_code = 1
    else:user_state_code = 0
    return user_state_code

class _QidianForHtml(BaseParser):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str, Any]] | None:
        soup = BeautifulSoup(content, 'lxml')
        script_list = soup.find_all('script')
        result = []
        for script in script_list:
            if "g_data.listInfo=" in str(script):
                script_str = script.get_text()
                start_index = script_str.find('g_data.listInfo=')+len('g_data.listInfo=')
                end_index = script_str.find(",g_data.page=")
                json_str = script_str[start_index:end_index]
                json_data = json.loads(json_str)
                for book_data in json_data:
                    book_name = book_data.get('bookName')
                    description = book_data.get('algInfo')
                    book_url = "https:" + book_data.get('bookUrl')
                    tags = book_data.get('chanName') + book_data.get('bookStatus')
                    latest_time_str = book_data.get('updateTime')
                    latest_chapter = book_data.get('lastChapterName')
                    book_img_url = "https:" + book_data.get('imgUrl')
                    need_unlock = bool(book_data.get('isVip'))
                    author_name = book_data.get('authorName')
                    word_count = book_data.get('wordsCnt')
                    result.append({
                            "name":book_name,
                            "author":author_name,
                            "tags":tags,
                            "word_count":word_count,
                            "description":description,
                            "latest_chapter":latest_chapter,
                            "update_time": latest_time_str,
                            "cover_url": book_img_url,
                            "book_url":book_url,
                            "need_unlock":need_unlock,
                            "platform":"起点中文网"
                        })

    def parse_novel_info(self, content, **kwargs) -> Novel:

        url = kwargs.get("url")
        soup = BeautifulSoup(content, 'lxml')
        # 获取网页内容
        name = soup.find('h1', id='bookName').get_text()
        if soup.find('div', class_='author-information'):  # 判断是否为起点特殊页面，以作者图片是否显示为准
            author = soup.find('a', class_='writer-name').get_text()
            author_desc = soup.find('div', class_='outer-intro').find('p').get_text()
            attribute_str = soup.find('p', class_='book-attribute').text
            attribute = attribute_str.split('·')
            label = [i.get_text() for i in soup.find('p', class_='all-label').find_all('a')]
            attribute.extend(label)  # 标签
            all_label = attribute
            intro = soup.find('p', class_='intro').get_text()
        else:
            intro = None
            author_desc = None
            all_label = []
            author = soup.find('span', class_='author').get_text()
        count_word_str = soup.find('p', class_='count').find('em').get_text()
        if count_word_str.endswith("万"):
            count_word = int(float(count_word_str[:-1])*10000)
        else:
            count_word = int(count_word_str)
        last_update_chapter = soup.find('a', class_='book-latest-chapter').get_text()[5:]
        last_update_time_str = soup.find('span',class_="update-time").get_text()
        last_update_time = time.mktime(time.strptime(last_update_time_str[5:], "%Y-%m-%d %H:%M:%S"))
        intro_detail = soup.find('p', id='book-intro-detail').get_text()  # 简介
        abstract = f'{intro}\n{intro_detail}'
        book_cover_url = 'https:' + soup.find('a', id='bookImg').find('img').get('src')  # 封面图片链接
        book_cover_data = requests.get(book_cover_url).content
        novel = Novel(url=url,
                      author=author,
                      name=name,
                      author_description=author_desc,
                      tags=all_label,
                      description=abstract,
                      count=count_word,
                      last_update_chapter=last_update_chapter,
                      last_update_time=last_update_time,
                      cover_image_data=book_cover_data
                      )

        # 获取章节列表
        chapters_items = soup.find('div', class_='catalog-all')
        order = 1
        for chapters_item in chapters_items:
            if type(chapters_item) is Tag:
                volume = chapters_item.find('h3', class_='volume-name').get_text().split("·")[0]
                title_list = [item.text for item in chapters_item.find_all("a",class_="chapter-name")]
                url_list = ["https:" + item.get("href") for item in chapters_item.find_all("a", class_="chapter-name")]
                for title, chapter_url in zip(title_list, url_list):
                    chapter = Chapter(title=title,
                                      url=chapter_url,
                                      order=order,
                                      volume=volume)
                    novel.update(chapter)
                    order += 1
        novel.total = len(novel.chapters)
        return novel

    def parse_chapter_content(self, content, orders:list[int], **kwargs) -> tuple[Chapter | None]:
        url = kwargs.get('url')
        soup = BeautifulSoup(content, 'lxml')
        script_list = soup.find_all("script")
        for script in script_list:
            if "pageContext" in str(script):
                script_str = script.get_text()
                json_data = json.loads(script_str)
                is_complete = json_data["pageContext"]["pageProps"]["isInIsSafeCanary"]
                chapter_info = json_data["pageContext"]["pageProps"]["pageData"]["chapterInfo"]
                title = chapter_info["chapterName"]
                word_count = chapter_info["wordsCount"]
                update_time_stamp = chapter_info["updateTimestamp"]
                order = chapter_info["seq"]
                volume_name = chapter_info["extra"]["volumeName"]
                novel_content_soup = soup.find('main')
                if soup.find('div', class_='mt-16px'):
                    novel_content = '\n'.join([i.get_text().strip() for i in novel_content_soup])
                else:
                    novel_content = '\n'.join([i.get_text().strip() for i in novel_content_soup.find_all("span",class_ = "content-text")])
                chapter = Chapter(
                    title=title,
                    url=url,
                    volume=volume_name,
                    content=novel_content,
                    timestamp=update_time_stamp,
                    order=order,
                    count=word_count,
                    is_complete=is_complete,
                )
                return (chapter,)
        soup = BeautifulSoup(content, 'lxml')
        title = soup.find('h1', class_='title').get_text()
        count_word_str = soup.find("div", class_="relative").find_all('span',
                                                                      class_='group inline-flex items-center mr-16px')[
            -1].get_text().split()[-1]
        count_word = int(re.findall(r'\d+', count_word_str)[0])
        update_time_str = soup.find('span', class_='chapter-date').get_text()
        update_time = time.mktime(time.strptime(update_time_str, "%Y年%m月%d日 %H:%M"))
        novel_content_soup = soup.find('main')
        if soup.find('div', class_='mt-16px'):
            integrity = False
            novel_content = '\n'.join([i.get_text().strip() for i in novel_content_soup])
        else:
            integrity = True
            novel_content = '\n'.join(
                [i.get_text().strip() for i in novel_content_soup.find_all("span", class_="content-text")])
        # 更新小说信息
        chapter = Chapter(
            title=title,
            url=url,
            order=orders[0],
            timestamp=update_time,
            count=count_word,
            content=novel_content,
            is_complete=integrity,
        )
        return (chapter,)

class QidianForBrowser(_QidianForHtml):
    def __init__(self,downloader:ChromeDownloader|APIDownloader|RequestsDownloader, **kwargs):
        super().__init__(**kwargs)
        self.user_status = None
        self.batch_size = 1
        self.downloader = downloader

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str,Any]] | str | None:
        search_url = f"https://qidian.com/so/{content}.html"
        if page >= 1:
            next_page_xpath = f"/html/body/div[1]/div[3]/div[1]/div[4]/div[2]/div/div/ul/li[{page+1}]"
            self.downloader.page.ele(f"xpath:{next_page_xpath}").click()
        self.downloader.get(search_url)
        html = self.downloader.page.raw_data
        result = super().parse_search_info(content=html, page=page, download_choice=None, **kwargs)
        if not result:
            return None
        if download_choice is not None:
            book_url = result[download_choice]
            return book_url
        else:return result


    def parse_novel_info(self, content, **kwargs: str) -> Novel:
        html = self.downloader.get(url=content)
        self.user_status = user_status(html)
        kwargs["url"] = content
        return super().parse_novel_info(content=html, **kwargs)

    def parse_chapter_content(self, content, orders: list[int], **kwargs) -> tuple[Chapter|None]:
        download_url = self.novel[orders[0]].url
        kwargs["url"] = download_url
        html = self.downloader.get(url=download_url)
        self.user_status = user_status(html)
        return super().parse_chapter_content(content=html, orders=orders, **kwargs)

class QidianForReq(_QidianForHtml):
    def __init__(self,downloader:ChromeDownloader|APIDownloader|RequestsDownloader, **kwargs):
        super().__init__(**kwargs)
        self.user_status:int = -1
        self.novel = None
        self.downloader = downloader

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str, Any]] | None:
        raise FeatureNotSupportedError("起点中文网不支持Requests以获取搜索结果")

    def parse_novel_info(self, content, **kwargs) -> Novel:

        html = self.downloader.get(url=content)
        self.user_status = user_status(html)
        self.novel = super().parse_novel_info(content=html,**kwargs)
        return self.novel

    def parse_chapter_content(self, content, orders: list[int], **kwargs) -> tuple[Chapter|None]:
        download_url = self.novel[orders[0]].url
        kwargs["url"] = download_url
        html = self.downloader.get(url=download_url)
        return super().parse_chapter_content(content=html,orders=orders)

class QidianParser(BaseParser):
    def __init__(self,downloader:ChromeDownloader|APIDownloader|RequestsDownloader,**kwargs):
        super().__init__(**kwargs)
        if downloader.MODE == DownloadMode.BROWSER:
            self.__parser = QidianForBrowser(downloader = downloader,**kwargs)
        elif downloader.MODE == DownloadMode.API:
             raise (self.__class__.__name__,"API","起点中文网暂不支持API")
        elif downloader.MODE == DownloadMode.REQUESTS:
            self.__parser = QidianForReq(downloader = downloader, **kwargs)
        self.batch_size = self.__parser.batch_size
        self.__parser.downloader = downloader

    def update(self, novel: Novel = None, downloader: ChromeDownloader | APIDownloader | RequestsDownloader = None,
               **kwargs):
        if novel:
            self.__parser.novel = novel
        if downloader:
            self.__parser.downloader = downloader

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str,Any]] | str | None:
        return self.__parser.parse_search_info(content=content, page=0, download_choice=download_choice, **kwargs)
    def parse_novel_info(self, content, **kwargs: str) -> Novel:
        return self.__parser.parse_novel_info(content=content)
    def parse_chapter_content(self, content, orders: list[int], **kwargs: list) -> tuple[Chapter|None]:
        return self.__parser.parse_chapter_content(content=content, orders=orders, **kwargs)