import base64
import random
import time

import requests
import winsound
from DrissionPage.errors import BaseError, WaitTimeoutError
from bs4 import BeautifulSoup
from colorama import Fore
from win10toast import ToastNotifier


class Qidian:
    def __init__(self, logger_, class_config, class_driver):

        self.logger = logger_
        self.img_items = {}
        self.down_url_list = []
        self.down_title_list = []
        self.pro_url = ''
        self.all_url_list = []
        self.all_title_list = []
        self.desc_figural = {}
        self.novel = {'version': '1.1.0', 'info': {}, 'chapters': {}}
        self.user_state_code = -1  # 用户状态码 -1:未登录状态； 1：标准
        self.Class_Config = class_config
        self.Class_Driver = class_driver

    def user_state_for_html(self, html):
        soup = BeautifulSoup(html, 'lxml')
        user_info_div = soup.find("div", class_="ml-auto text-s-gray-900 text-bo2 relative group")
        if user_info_div.find('Button'):
            self.user_state_code = -1
        if user_info_div.find("a", class_="block flex items-center hover:text-primary-red-500 py-10px px-32px"):
            self.user_state_code = 1
        match self.user_state_code:
            case -1:
                print(f"{Fore.YELLOW}起点账号未登录")
            case 1:
                print(f"{Fore.GREEN}起点账号已登录")
        pass

    def _get_soup_for_browser(self, url):
        if "book" in url:
            class_name = "#bookCatalogSection"
        elif "chapter" in url:
            class_name = ".content-text"
        else:
            class_name = None
        try:
            self.Class_Driver.tab.get(url)
            time.sleep(random.randint(self.Class_Config.Delay[0], self.Class_Config.Delay[1]))
            if not self.Class_Driver.tab.states.is_alive: raise BaseError
            self.Class_Driver.tab.wait.eles_loaded(
                class_name, raise_err=True)  # 起点目录页、起点章节内容页（class）
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

    def get_page(
            self,
            url: str,
    ):
        soup = BeautifulSoup(self._get_soup_for_browser(url), 'lxml')
        self.novel = {'version': '1.1.0', 'info': {}, 'chapters': {}}
        if soup.find('div', class_='wrap error-wrap'):
            print('Cannot find this book')
            return False
        # 获取网页内容
        name = soup.find('h1', id='bookName').get_text()
        author = soup.find('span', class_='author').get_text()
        author_desc = 'None'
        """            BeautifulSoup(requests.get('https:' + soup.find('a', class_='author-img').get('href'), headers={
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0',
            'referer': 'https://www.qidian.com/',
            'Cookie': "; ".join([f"{c['name']}={c['value']}" for c in driver.get_cookies()])}).text, 'lxml').find(
            'div', class_='header-msg-desc').text)
"""
        attribute = soup.find('p', class_='book-attribute').text
        label = ' '.join([i.get_text() for i in soup.find('p', class_='all-label').find_all('a')])
        all_label = attribute + label  # 标签
        count_word = soup.find('p', class_='count').find('em').get_text() + '字'
        last_update = soup.find('a', class_='book-latest-chapter').get_text()
        intro = soup.find('p', class_='intro').get_text()
        intro_detail = soup.find('p', id='book-intro-detail').get_text()  # 简介
        abstract = f'{intro}\n{intro_detail}'
        book_cover_url = 'https:' + soup.find('a', id='bookImg').find('img').get('src')  # 封面图片链接
        book_cover_data = base64.b64encode(requests.get(book_cover_url).content).decode("utf-8")
        self.desc_figural[name] = book_cover_url
        web_chapter_list = soup.find_all('li', class_='chapter-item')
        # 更新小说信息
        self.novel['info']['name'] = name
        self.novel['info']['author'] = author
        self.novel['info']['author_desc'] = author_desc
        self.novel['info']['label'] = all_label
        self.novel['info']['count_word'] = count_word
        self.novel['info']['last_update'] = last_update
        self.novel['info']['abstract'] = abstract
        self.novel['info']['book_cover_data'] = "data:image/png;base64," + book_cover_data
        self.novel['info']['url'] = url
        self.img_items['封面图片'] = {name: self.novel['info']['book_cover_data']}
        # 获取章节列表
        self.all_title_list = [title.find('a').get_text() for title in web_chapter_list]
        self.all_url_list = ['https:' + title.find('a').get('href') for title in web_chapter_list]
        self.pro_url = 'https:' + soup.find('a', class_='blue-btn-detail J-getJumpUrl').get('href')  # 阅读进度
        # 更新下载列表
        self.down_url_list, self.down_title_list = self.all_url_list, self.all_title_list
        return True

    def download(self, title, chapter_url, index=0, page_url=None):
        html = self._get_soup_for_browser(chapter_url)
        soup = BeautifulSoup(html, 'lxml')
        count_word = \
        soup.find('span', class_='group inline-flex items-center mr-16px').get_text().replace('123 ', '').split()[1]
        update_time = soup.find('span', class_='chapter-date').get_text()
        novel_content = soup.find_all('span', class_='content-text')
        novel_content = '\n'.join([i.get_text() for i in novel_content])
        if soup.find('section',
                     class_='sm:border-t sm:border-outline-black-8 sm:pt-48px sm:my-64px sm:mx-64px mb-24px text-center mx-20px'):
            integrity = False
        else:
            integrity = True
        # 更新小说信息
        self.novel['chapters'][title] = {
            'url': chapter_url,
            'update': update_time,
            'count_word': count_word,
            'content': novel_content.replace('已经是最新一章', ''),
            'integrity': integrity,
            'img_item': {}
        }

        return self.novel
