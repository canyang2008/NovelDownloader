import time
import random
from DrissionPage.errors import BaseError
from bs4 import BeautifulSoup

class GetHtml:
    def __init__(self, logger, rundriver):

        self.logger = logger
        self.RunDriver = rundriver
        self.driver = None
        self.Class_Config = None
        self.soup = None

    def get(self,
            url: str,
            driver,
            wait_time: tuple[int, int] = (0, 0),
            ):
        if "page" in url:
            class_name = ".page-directory-content"
        elif "reader" in url:
            class_name = ".muye-reader-content noselect"
        elif "book" in url:
            class_name = ".page-directory-content"
        elif "chapter" in url:
            class_name = ".content-text"
        else:
            print("无效的url")
            exit(1)
        try:
            driver.get(url)
            time.sleep(random.randint(wait_time[0], wait_time[1]))
            if not driver.states.is_alive: raise BaseError
            driver.wait.eles_loaded(
                class_name, raise_err=True)  # 分别为番茄目录页、起点目录页、番茄章节内容页、起点章节内容页（class）
            html = driver.raw_data
            self.soup = BeautifulSoup(html, "lxml")
            return self.soup
        except BaseError:
            driver = self.RunDriver.run()
            return self.get(url, driver, wait_time)
