import random
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import field
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from novel_downloader.models import DownloadMode


class ThreadingTimeout:
    def __init__(self, seconds):
        self.seconds = seconds
        self.timer = None
        self.timed_out = False

    def __enter__(self):
        self.timed_out = False
        self.timer = threading.Timer(self.seconds, self._timeout)
        self.timer.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer:
            self.timer.cancel()
        if self.timed_out:
            raise TimeoutError(f"Operation timed out after {self.seconds} seconds")
        return False

    def _timeout(self):
        self.timed_out = True


class BaseDownloader(ABC):
    """下载器基类"""
    @abstractmethod
    def __init__(self, delay, timeout, interval, max_retry, **kwargs):
        self.delay = delay
        self.MODE = None
        self.interval = interval
        self.timeout = timeout
        self.max_retry = max_retry
        self.index = 0
        self.page = None

    @abstractmethod
    def get(self, url, **kwargs):
        """访问网站"""
        pass

    def __del__(self):
        if self.page:
            self.page.close()

class ChromeDownloader(BaseDownloader):
    """Chrome下载器"""

    def __init__(
            self,
            delay,
            timeout,
            max_retry,
            interval,
            port,
            headless,
            user_data_dir,
            **kwargs
        ):
        super().__init__(delay=delay, timeout=timeout, interval=interval, max_retry=max_retry,**kwargs)

        self.headless = headless
        self.MODE = DownloadMode.BROWSER
        self.user_data_dir = user_data_dir
        self.port = port

        self.driver = self.__init_driver()
        self.__set_new_tab()

    def __init_driver(self):
        """初始化浏览器驱动"""

        from DrissionPage import Chromium, ChromiumOptions
        co = ChromiumOptions()
        co = co.set_user_data_path(self.user_data_dir)
        co = co.set_local_port(self.port)
        co = co.headless(self.headless)
        self.driver = Chromium(addr_or_opts=co)
        return self.driver

    def __set_new_tab(self):
        from DrissionPage.common import Settings
        Settings.set_singleton_tab_obj(False)
        self.page = self.driver.new_tab()

    def get(self, url, **kwargs):
        """访问网站"""
        time.sleep(random.uniform(*self.delay))
        try:
            self.page.get(url)
            try:
                with ThreadingTimeout(self.timeout):
                    response:str = self.page.raw_data
            except TimeoutError:
                retry = kwargs.get("retry",1)
                if retry <= self.max_retry:
                    kwargs["retry"] = retry + 1
                    return self.get(url,**kwargs)
                else:
                    raise TimeoutError(f"Operation timed out after {self.max_retry} seconds")
            return response

        except TimeoutError:
            raise TimeoutError(f"Operation timed out after {self.max_retry} seconds")

class APIDownloader(BaseDownloader):
    """API下载器"""
    def __init__(
            self,
            delay,
            timeout,
            max_retry,
            interval,
            params,
            api_address,
            headers,
            api_key,
            endpoint,
            **kwargs
    ):
        super().__init__(delay=delay, timeout=timeout, interval=interval, max_retry=max_retry,**kwargs)
        self.current_cookies = None

        self.key = api_key
        self.endpoint = endpoint
        self.headers = headers
        self.api_address = api_address
        self.MODE = DownloadMode.API


        self.__set_new_session()
        if not self.headers:
            self.headers:dict[str, str] = field(default_factory=lambda:{
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            })

    def __set_new_session(self):
        retry_strategy = Retry(
            total=3,
            backoff_factor=self.interval - 1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.page = requests.Session()
        self.page.mount("https://", adapter)

    def get(self, url, **kwargs):
        """访问网站"""
        time.sleep(random.uniform(*self.delay))
        try:
            with ThreadingTimeout(self.timeout):
                response = self.page.post(url=url, data=kwargs["post_data"], timeout=self.timeout)
            response.encoding = 'utf-8'
            if not self.page.cookies:
                self.current_cookies = response.cookies
                self.page.cookies = self.current_cookies
            return response.json()

        except TimeoutError:
            retry = kwargs.get("retry",1)
            if retry <= self.max_retry:
                kwargs["retry"] = retry + 1
                self.get(url,**kwargs)

class RequestsDownloader(BaseDownloader):
    """Requests下载器"""

    def __init__(
            self,
            delay,
            timeout,
            max_retry,
            interval,
            cookies,
            headers,
            proxies,
            **kwargs
    ):
        super().__init__(delay=delay, timeout=timeout, interval=interval, max_retry=max_retry,**kwargs)
        self.current_cookies = None
        self.cookies = cookies
        self.proxies = proxies
        self.headers = headers
        self.MODE = DownloadMode.REQUESTS

        if not self.headers:
            from fake_useragent import UserAgent
            ua = UserAgent()
            self.headers:dict[str, str] = {
                'User-Agent': ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Cache-Control': 'max-age=0',
    }
        self.__set_new_session()

    def __set_new_session(self):
        retry_strategy = Retry(
            total=3,
            backoff_factor=self.interval - 1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.page = requests.Session()
        self.page.mount("https://", adapter)
        self.page.proxies = self.proxies
        self.page.headers = self.headers
        from http.cookies import SimpleCookie
        cookie = SimpleCookie()
        cookie.load(self.cookies)
        cookies_dict = {key: morsel.value for key, morsel in cookie.items()}
        self.page.cookies.update(cookies_dict)

    def get(self, url, **kwargs):
        """访问网站"""
        time.sleep(random.uniform(*self.delay))
        try:
            with ThreadingTimeout(self.timeout):
                response = self.page.get(url, timeout=self.timeout)
            response.encoding = 'utf-8'
            if not self.page.cookies:
                self.current_cookies = response.cookies
                self.page.cookies = self.current_cookies
            return response.text
        except TimeoutError:
            retry = kwargs.get("retry",1)
            if retry <= self.max_retry:
                kwargs["retry"] = retry + 1
                self.get(url, **kwargs)
                
class DownloaderFactory:
    """下载器工厂"""

    @staticmethod
    def create_downloader(mode:DownloadMode = DownloadMode.BROWSER,
                          count = 3,
                          delay = (3,5),
                          timeout = 10,
                          max_retry = 3,
                          interval = 2,

                          port = 9445,
                          headless = False,
                          user_data_dir = None,

                          address = None,
                          api_key = None,
                          endpoint = None,
                          params = None,

                          cookies = None,
                          headers = None,
                          proxies = None,
                          ) -> tuple[ChromeDownloader|APIDownloader|RequestsDownloader,...]:
        """创建下载器"""
        result = []
        for i in range(count):
            if mode == DownloadMode.BROWSER:
                result.append(ChromeDownloader(
                    delay = delay,
                    timeout = timeout,
                    max_retry = max_retry,
                    interval = interval,
                    port = port,
                    headless = headless,
                    user_data_dir = user_data_dir,
                ))
            elif mode == DownloadMode.API:
                result.append(APIDownloader(
                    delay = delay,
                    timeout = timeout,
                    max_retry = max_retry,
                    interval = interval,
                    api_address = address,
                    params=params,
                    headers = headers,
                    api_key = api_key,
                    endpoint = endpoint,
                ))
            elif mode == DownloadMode.REQUESTS:
                result.append(RequestsDownloader(
                    delay,
                    timeout,
                    max_retry,
                    interval,
                    cookies,
                    headers,
                    proxies,
                ))
            else:
                raise ValueError(f"不支持的下载模式: {mode}")
        return tuple(result)
