import random
import time

import winsound
from DrissionPage.errors import BaseError, WaitTimeoutError
from bs4 import BeautifulSoup
from win10toast import ToastNotifier


class GetHtml:
    def __init__(self, rundriver, play_sound, logger_):

        self.logger = logger_
        self.RunDriver = rundriver
        self.driver = None
        self.play_sound = play_sound
        self.soup = None

    def get(self,
            url: str,
            tab,
            wait_time: tuple[int, int] = (0, 0),
            ):
        if "page" in url:
            class_name = ".page-directory-content"
        elif "reader" in url:
            class_name = ".muye-reader-content noselect"
        elif "book" in url:
            class_name = "#bookCatalogSection"
        elif "chapter" in url:
            class_name = ".content-text"
        else:
            print("无效的url")
            exit(1)
        try:
            tab.get(url)
            time.sleep(random.randint(wait_time[0], wait_time[1]))
            if not tab.states.is_alive: raise BaseError
            tab.wait.eles_loaded(
                class_name, raise_err=True)  # 分别为番茄目录页、起点目录页、番茄章节内容页、起点章节内容页（class）
            html = tab.raw_data
            self.soup = BeautifulSoup(html, "lxml")
            return self.soup
        except WaitTimeoutError:
            if tab.get_frames():
                toast = ToastNotifier()
                toast.show_toast(
                    title="验证码拦截",
                    msg="请完成验证码",
                    icon_path=None,
                    duration=3
                )
                if self.play_sound:
                    winsound.MessageBeep(winsound.MB_OK)
                    time.sleep(1)
                    winsound.MessageBeep(winsound.MB_OK)
                input("请完成验证码...\n完成后按Enter继续")
                return self.get(url, tab, wait_time)
        except BaseError:
            tab = self.RunDriver.run()
            return self.get(url, tab, wait_time)
