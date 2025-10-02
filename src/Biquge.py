import random
import re
import time

import requests
import winsound
from DrissionPage.errors import BaseError, WaitTimeoutError
from bs4 import BeautifulSoup
from colorama import Fore
from win10toast import ToastNotifier


class Biquge:
    def __init__(self, logger_, class_config, class_driver):

        self.Class_Driver = None
        self.logger = logger_
        self.down_url_list = []
        self.down_title_list = []
        self.pro_url = ''
        self.all_url_list = []
        self.all_title_list = []
        self.novel = {'version': '1.1.0', 'info': {}, 'chapters': {}, "config": {}}
        self.img_items = {}
        self.Class_Config = None
        self.user_state_code = -1  # 用户状态码 -1:未登录状态；1：标准
        self.Class_Config = class_config
        self.Class_Driver = class_driver

    def user_state_for_html(self, html):
        soup = BeautifulSoup(html, 'lxml')
        # 右上角登录界面
        user_info_div = soup.find("div", class_="nri")
        if user_info_div is None:
            self.user_state_code = -1
        else:
            self.user_state_code = 1

        match self.user_state_code:
            case -1:
                print(f"{Fore.YELLOW}笔趣阁账号未登录")
            case 1:
                print(f"{Fore.GREEN}笔趣阁账号已登录")

    def _get_soup_for_browser(self, url):
        try:
            self.Class_Driver.tab.get(url)
            time.sleep(random.uniform(self.Class_Config.Delay[0], self.Class_Config.Delay[1]))
            if not self.Class_Driver.tab.states.is_alive: raise BaseError
            html = self.Class_Driver.tab.raw_data
            return html
        except WaitTimeoutError:
            # 应该没有验证码啊框架吧..算了，复制粘贴进去先
            if self.Class_Driver.tab.get_frames():
                toast = ToastNotifier()
                toast.show_toast(
                    title="验证码拦截",
                    msg="请完成验证码",
                    icon_path=None,
                    duration=3
                )
                if self.Class_Config.Play_completion_sound:
                    winsound.MessageBeep(winsound.MB_OK)
                    time.sleep(1)
                    winsound.MessageBeep(winsound.MB_OK)
                input("请完成验证码...\n完成后按Enter继续")
                return self._get_soup_for_browser(url)
        except BaseError:
            self.Class_Driver.tab = self.Class_Driver.run()
            return self._get_soup_for_browser(url)
        return True

    def _get_page_for_html(
            self,
            url: str,
            html
    ):
        label = ""
        last_update_for_chapter, last_update_for_time = None, None
        self.novel = {'version': '1.1.0', 'info': {}, 'chapters': {}, "config": {}}
        soup = BeautifulSoup(html, 'html.parser')
        info_data = soup.find("div", id="info")     # 信息
        name = info_data.find("h1").get_text()
        p_list = info_data.find_all("p")
        author = ""
        for p in p_list:
            if p.text.startswith("作  者："):
                author = p.find("a").get_text()
            if p.text.startswith("分  类："):
                label = p.find("a").get_text()
            if p.text.startswith("最后更新："):
                last_update_for_time = p.get_text()
            if p.text.startswith("最新更新："):
                last_update_for_chapter = p.get_text()
        last_update = f"{last_update_for_chapter} {last_update_for_time}"
        book_cover_url = soup.find("div", id="fmimg").find("img").get("src")
        book_cover_data = ''#base64.b64encode(requests.get(book_cover_url).content).decode("utf-8") # 访问会卡在这里
        web_chapter_list = soup.find('div', id='list').find_all('dd')
        # 更新小说信息
        self.novel['info']['name'] = name
        self.novel['info']['author'] = author
        self.novel['info']['author_desc'] = ""
        self.novel['info']['label'] = label
        self.novel['info']['count_word'] = ""
        self.novel['info']['last_update'] = last_update
        self.novel['info']['abstract'] = soup.find("div", id="intro").get_text()
        self.novel['info']['book_cover_data'] = "data:image/png;base64," + book_cover_data
        self.novel['info']['url'] = url
        self.img_items['封面图片'] = {name: self.novel['info']['book_cover_data']}
        # 更新下载列表
        self.all_title_list = [title.find("a").get("title") for title in web_chapter_list]
        self.all_url_list = ["https://www.biqugequ.org/" + url.find("a").get("href") for url in web_chapter_list]
        self.down_url_list, self.down_title_list = self.all_url_list, self.all_title_list
        return True

    def _get_novel_for_html(self, title, chapter_url, html):
        # 笔趣阁，一章分多页面设计
        url_id = re.findall(r"(\d+).html", chapter_url)
        novel_content = ""
        while True:
            soup = BeautifulSoup(html, 'lxml')
            novel_content_div = soup.find('div', id='content').find_all("p")
            for p in novel_content_div[:-1]:
                novel_content += p.get_text()+'\n'
            next_url = soup.find("div", class_="bottem2").find("a", id="pager_next").get("href")
            # 当下一页是当前章节的下一页时
            if re.search(rf"{url_id}_\d.html", next_url):
                next_url = "https://www.biqugequ.org" + next_url
                if self.Class_Config.Get_mode == 0:  # 浏览器模式
                    html = self._get_soup_for_browser(next_url)     # 获取html
                else:
                    html = requests.get(next_url).text
                continue
            else:
                break
        self.novel['chapters'][title] = {
            'url': chapter_url,
            'update': "",
            'count_word': "",
            'content': novel_content,
            'integrity': True,
            'img_item': {}
        }

    def get_page(self, url):  # 获取小说info和所有链接与标题
        url = url.split(".html")[0]     # 访问有完整目录的目录页
        if self.Class_Config.Get_mode == 0:  # 浏览器模式
            html = self._get_soup_for_browser(url)
            self.user_state_for_html(html)  # 用户状态
        else:
            html = requests.get(url).text
            if '<div id="list">' not in html:
                print("获取所有目录页出现问题")
                return False
        self._get_page_for_html(url, html)
        return True

    def download(self, title, chapter_url, index=0, page_url=None):
        html = self._get_soup_for_browser(chapter_url)
        self._get_novel_for_html(title, chapter_url, html)
        return True
