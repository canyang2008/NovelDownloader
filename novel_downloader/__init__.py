import time
import importlib
import os
import threading
from typing import Dict, Any
from dataclasses import asdict
from typing import Iterable
from novel_downloader.models import DownloadMode, Website
from novel_downloader.models.group import Group
from novel_downloader.models.novel import Novel, Chapter
from novel_downloader.core.storage import NovelStorage
from novel_downloader.parsers import parse_url
from novel_downloader.core.downloader import (
    ChromeDownloader,
    APIDownloader,
    RequestsDownloader,
    DownloaderFactory
)
from novel_downloader.models.config import (
    UserConfig,
    SiteApiConfig,
    ApiProviderConfig,
    SiteRequestsConfig
)
from novel_downloader.models.save import (
    SaveMethodConfig,
    BaseSaveConfig
)
from novel_downloader.outputs import (
    dir_transform,
    sanitize_name
)
class NovelDownloader:
    """小说下载器主类"""
    thread_lock = threading.Lock()
    def __init__(self, config_method: int):

        self._group_dict = None
        from novel_downloader.core.config import ConfigManager1,ConfigManager2
        if config_method == 1:
            self.config_manager = ConfigManager1()
            self.config = self.config_manager.config
        elif config_method == 2:
            self.config_manager = ConfigManager2()
            self.config = self.config_manager.config
        else:
            self.config = UserConfig()
        self.novel = None
        self.downloaders: list[ChromeDownloader | APIDownloader | RequestsDownloader] | None = None
        # 加载解析器
        self.parser = None
        self.all_parsers = self._load_parsers()
        self.website_parsers = []

        # 多线程
        self.thread_count = None
        self.__download_lock = threading.Lock()

        self.__added_save_novel = False

        self.enable_outputs = {}
        self.save_method_config = SaveMethodConfig()
        self._runtime_params = {}

    @staticmethod
    def _load_parsers() -> Dict[str, Any]:
        """动态加载解析器"""
        all_parsers = {}
        parsers_dir = os.path.join(os.path.dirname(__file__), 'parsers')
        for file in os.listdir(parsers_dir):
            if file.endswith('.py') and file not in ['__init__.py', 'base.py']:
                module_name = file[:-3]
                with open(os.path.join("novel_downloader","parsers",file),encoding="utf-8") as f:
                    floor=0
                    for line in f:
                        floor+=1
                        if line.strip() != "enable=False" and floor==1:
                            try:
                                module = importlib.import_module(f'novel_downloader.parsers.{module_name}', __name__)
                                parser_class = getattr(module, f'{module_name.capitalize()}Parser')
                                all_parsers[module_name] = parser_class
                            except (ImportError, AttributeError) as e:
                                print(f"load parser {module_name} failed: {e}")
                        else:break

        return all_parsers
    @staticmethod
    def read_novel(file_path:str):
        if os.path.exists(file_path):
            novel_list = NovelStorage.read_novel_data(file_path)
            return novel_list
        else:return None

    def search_novel(self, website:Website, search_key:str, page:int=0,download_choice=None) -> dict:
        parser = self.all_parsers.get(website.value)(downloader=self.downloaders[0])
        return parser.parse_search_info(content=search_key, page=page, download_choice=download_choice)

    def get_info(self, url) -> Novel:
        """获取小说信息"""
        origin_url = url
        url, website = parse_url(origin_url)
        if self.parser is None:
            self.parser = self.all_parsers.get(website.value)(downloader=self.downloaders[0])
        self.novel = self.parser.parse_novel_info(content=url)
        self.website_parsers = []
        for i in range(self.thread_count):
            parser = self.all_parsers.get(website.value)(downloader=self.downloaders[i])
            parser.update(novel = self.novel,downloader = self.downloaders[i])
            self.website_parsers.append(parser)
        self._group_dict["novel_name"] = self.novel.name
        self._group_dict["url"] = self.novel.url
        self._group_dict["file_path"] = os.path.join("data", "Local",self._runtime_params["group"],"json", f"{self.novel.name}.json")
        self._group_dict["save_method"] = SaveMethodConfig(
            **{file_format:save_method.save_config for file_format,save_method in self.enable_outputs.items()}
        )
        group = Group(**self._group_dict)
        self.novel.group = group
        return self.novel

    def get_chapters(self, download_url, orders, choice=0) -> tuple[Chapter]:
        """下载单个章节"""
        if self.novel is None:
            raise AttributeError("novel is None")
        chapters =  self.website_parsers[choice].parse_chapter_content(content=download_url, orders=orders)
        if chapters:
            self.thread_lock.acquire()
            self.novel.update(chapters)
            self.thread_lock.release()
        return chapters

    def add_save(self, save_format:str, dir_name:str, file_name:str, **kwargs):
        output_module = importlib.import_module(f'novel_downloader.outputs.{save_format}', __name__)
        output_class = getattr(output_module, f'{save_format.upper()}Output')
        save_config_module = importlib.import_module(f"novel_downloader.models.save", __name__)
        save_config_class = getattr(save_config_module, f'{save_format.capitalize()}SaveConfig')
        save_config = save_config_class(output_dir=dir_name,file_name=file_name)
        if kwargs:
            attrs = dir(BaseSaveConfig)
            for attr in attrs:
                if kwargs.get(attr) is not None:
                    setattr(save_config,attr, kwargs.get(attr))

            base_output = output_class(save_config)
            self.enable_outputs[save_format] = base_output
            setattr(self.save_method_config,"base",save_config)

    def save_novel(self, chapters: Iterable[Chapter]| None = None) -> bool:
        """保存小说"""
        if chapters is None: chapters = []
        if self.novel is None:
            raise AttributeError("novel is None")
        elif not self.__added_save_novel:
            for v in self.enable_outputs.values():
                if v.save_config.file_name is None:
                    v.save_config.file_name = self.novel.name
                v.save_config.output_dir = dir_transform(
                    v.save_config.output_dir,
                    self.config.user,
                    self._runtime_params["group"],
                    self.novel.name
                )
            self.__added_save_novel = True
            for v in self.enable_outputs.values():
                v.novel = self.novel
        for v in self.enable_outputs.values():
            v.save(chapters=chapters)
        return True

    def save_config(self):
        self.config_manager.save_config()
        pass

    def read_groups(self, path=None):
        self.config.groups = self.config_manager.parse_group(path)
        return self.config.groups

    def set(self, config: UserConfig | Group | None = None, group: str = None, mode: DownloadMode = None,
            thread_count: int = None, delay: list[float] = None, timeout: int = None, max_retry: int = None,
            interval: float = None, port: int = None, headless: bool = None, user_data_dir: str = None,
            api_name: str = None, api_address: str = None, api_key: str = None, endpoint: str = None,
            params: dict[str, Any] = None, website: Website = None, cookies: str = None, headers: dict = None,
            proxies: dict[str, str] = None, save_configs: dict[str, Any] = None, backup_auto: bool = None,
            backup_interval: int = None, backup_dir: str = None, backup_name: str = None,
            backup_pop_up_folder: bool = None, backup_max_backups: int = None, update_config=False,create_if_missing: bool = True, **kwargs):
        """
        设置下载器参数，优先级：显式参数 > config 对象 > 基准源 > 内置默认值。
        - 当 update_config=True 时，基准源为 self.config，且最终参数会写入 self.config 和 self._runtime_params。
        - 当 update_config=False 时，基准源为 self._runtime_params（若不存在则回退到 self.config），最终参数仅写入 self._runtime_params。
        """
        # ------------------------------------------------------------
        # 确定最终模式
        # ------------------------------------------------------------
        final_mode = mode
        website = str(website)
        if final_mode is None:
            if config is not None and hasattr(config, 'mode') and config.mode is not None:
                final_mode = config.mode
            else:
                final_mode = self.config.mode
        final_website = website

        # ------------------------------------------------------------
        # 辅助函数：从 UserConfig/Group 中获取参数值（与之前相同）
        # ------------------------------------------------------------
        def get_from_source(source, param_name, mode=None, website=None, api_name=None):
            """从 source (UserConfig/Group/None) 获取 param_name 的值"""
            if source is None:
                return None
            if isinstance(source, Group):
                return getattr(source, param_name, None)
            if isinstance(source, UserConfig):
                # 顶层字段
                if param_name in ['group', 'mode', 'thread_count', 'readme', 'play_sound', 'version']:
                    return getattr(source, param_name, None)
                # 浏览器特有字段
                if param_name in ['port', 'headless', 'user_data_dir']:
                    return getattr(source.browser, param_name, None)
                # 通用下载参数
                if param_name in ['timeout', 'max_retry', 'interval', 'delay']:
                    if mode == DownloadMode.BROWSER:
                        return getattr(source.browser, param_name, None)
                    elif mode == DownloadMode.API and website:
                        site_api = source.api.get(website)
                        if site_api:
                            provider = None
                            if api_name and api_name in site_api.providers:
                                provider = site_api.providers[api_name]
                            else:
                                provider = site_api.get_provider()
                            if provider:
                                return getattr(provider, param_name, None)
                    elif mode == DownloadMode.REQUESTS and website:
                        site_req = source.requests.get(website)
                        if site_req:
                            return getattr(site_req, param_name, None)
                # API 特有参数
                if param_name in ['api_address', 'api_key', 'endpoint', 'params']:
                    if mode == DownloadMode.API and website:
                        site_api = source.api.get(website)
                        if site_api:
                            provider = None
                            if api_name and api_name in site_api.providers:
                                provider = site_api.providers[api_name]
                            else:
                                provider = site_api.get_provider()
                            if provider:
                                mapping = {'api_address': 'address', 'api_key': 'key',
                                           'endpoint': 'endpoint', 'params': 'params'}
                                return getattr(provider, mapping[param_name], None)
                # Requests 特有参数
                if param_name in ['cookies', 'headers', 'proxies']:
                    if mode == DownloadMode.REQUESTS and website:
                        site_req = source.requests.get(website)
                        if site_req:
                            return getattr(site_req, param_name, None)
                # 保存参数
                if param_name == "save_method":
                    return source.save_method
                # 备份参数
                if param_name.startswith('backup_'):
                    attr = param_name[7:]
                    return getattr(source.backup, attr, None)
            return None

        # ------------------------------------------------------------
        # 确定所有参数的最终值（存入 final 字典）
        # ------------------------------------------------------------
        final = {}

        # ---------- 通用参数 ----------
        # group
        if group is not None:
            final['group'] = group
        else:
            val = get_from_source(config, 'group')
            if val is None:
                # 从基准源读取
                if update_config:
                    base_val = get_from_source(self.config, 'group')
                else:
                    base_val = self._runtime_params.get('group')
                    if base_val is None:
                        base_val = get_from_source(self.config, 'group')
                val = base_val
            final['group'] = val if val is not None else "Default"

        final['mode'] = final_mode
        final['website'] = final_website

        # thread_count
        if thread_count is not None:
            final['thread_count'] = thread_count
        else:
            val = get_from_source(config, 'thread_count')
            if val is None:
                if update_config:
                    base_val = get_from_source(self.config, 'thread_count')
                else:
                    base_val = self._runtime_params.get('thread_count')
                    if base_val is None:
                        base_val = get_from_source(self.config, 'thread_count')
                val = base_val
            final['thread_count'] = val if val is not None else 3

        # ---------- 通用下载参数 ----------
        for param in ['timeout', 'max_retry', 'interval']:
            param_val = locals()[param]
            if param_val is not None:
                final[param] = param_val
            else:
                val = get_from_source(config, param, mode=final_mode, website=final_website, api_name=api_name)
                if val is None:
                    if update_config:
                        base_val = get_from_source(self.config, param, mode=final_mode, website=final_website,
                                                   api_name=api_name)
                    else:
                        base_val = self._runtime_params.get(param)
                        if base_val is None:
                            base_val = get_from_source(self.config, param, mode=final_mode, website=final_website,
                                                       api_name=api_name)
                    val = base_val
                defaults = {'timeout': 10, 'max_retry': 3, 'interval': 2}
                final[param] = val if val is not None else defaults[param]

        # delay
        if delay is not None:
            final['delay'] = delay
        else:
            val = get_from_source(config, 'delay', mode=final_mode, website=final_website, api_name=api_name)
            if val is None:
                if update_config:
                    base_val = get_from_source(self.config, 'delay', mode=final_mode, website=final_website,
                                               api_name=api_name)
                else:
                    base_val = self._runtime_params.get('delay')
                    if base_val is None:
                        base_val = get_from_source(self.config, 'delay', mode=final_mode, website=final_website,
                                                   api_name=api_name)
                val = base_val
            if val and isinstance(val, list):
                val = (val[0], val[1])
            final['delay'] = val if val is not None else (3.0, 5.0)

        # ---------- 浏览器特定参数 ----------
        if port is not None:
            final['port'] = port
        else:
            val = get_from_source(config, 'port')
            if val is None:
                if update_config:
                    base_val = get_from_source(self.config, 'port')
                else:
                    base_val = self._runtime_params.get('port')
                    if base_val is None:
                        base_val = get_from_source(self.config, 'port')
                val = base_val
            final['port'] = val if val is not None else 9445

        if user_data_dir is not None:
            final['user_data_dir'] = user_data_dir
        else:
            val = get_from_source(config, 'user_data_dir')
            if val is None:
                if update_config:
                    base_val = get_from_source(self.config, 'user_data_dir')
                else:
                    base_val = self._runtime_params.get('user_data_dir')
                    if base_val is None:
                        base_val = get_from_source(self.config, 'user_data_dir')
                val = base_val
            final['user_data_dir'] = val if val is not None else ""

        if headless is not None:
            final['headless'] = headless
        else:
            val = get_from_source(config, 'headless')
            if val is None:
                if update_config:
                    base_val = get_from_source(self.config, 'headless')
                else:
                    base_val = self._runtime_params.get('headless')
                    if base_val is None:
                        base_val = get_from_source(self.config, 'headless')
                val = base_val
            final['headless'] = val if val is not None else False

        # ---------- API 特定参数 ----------
        api_params = ['api_address', 'api_key', 'endpoint', 'params']
        for param in api_params:
            param_val = locals()[param]
            if param_val is not None:
                final[param] = param_val
            else:
                val = get_from_source(config, param, mode=final_mode, website=final_website, api_name=api_name)
                if val is None:
                    if update_config:
                        base_val = get_from_source(self.config, param, mode=final_mode, website=final_website,
                                                   api_name=api_name)
                    else:
                        base_val = self._runtime_params.get(param)
                        if base_val is None:
                            base_val = get_from_source(self.config, param, mode=final_mode, website=final_website,
                                                       api_name=api_name)
                    val = base_val
                if param == 'params':
                    final[param] = val if val is not None else {}
                else:
                    final[param] = val if val is not None else ""

        # ---------- Requests 特定参数 ----------
        req_params = ['cookies', 'headers', 'proxies']
        for param in req_params:
            param_val = locals()[param]
            if param_val is not None:
                final[param] = param_val
            else:
                val = get_from_source(config, param, mode=final_mode, website=final_website, api_name=api_name)
                if val is None:
                    if update_config:
                        base_val = get_from_source(self.config, param, mode=final_mode, website=final_website,
                                                   api_name=api_name)
                    else:
                        base_val = self._runtime_params.get(param)
                        if base_val is None:
                            base_val = get_from_source(self.config, param, mode=final_mode, website=final_website,
                                                       api_name=api_name)
                    val = base_val
                final[param] = val if val is not None else ({} if param in ['headers', 'proxies'] else "")

        # ---------- 备份参数 ----------
        backup_params = ['backup_auto', 'backup_interval', 'backup_dir', 'backup_name',
                         'backup_pop_up_folder', 'backup_max_backups']
        for param in backup_params:
            param_val = locals()[param]
            if param_val is not None:
                final[param] = param_val
            else:
                val = get_from_source(config, param)
                if val is None:
                    if update_config:
                        base_val = get_from_source(self.config, param)
                    else:
                        base_val = self._runtime_params.get(param)
                        if base_val is None:
                            base_val = get_from_source(self.config, param)
                    val = base_val
                defaults = {
                    'backup_auto': False, 'backup_interval': 86400, 'backup_dir': 'C:\\',
                    'backup_name': 'Novel_backup.zip', 'backup_pop_up_folder': True, 'backup_max_backups': 10
                }
                final[param] = val if val is not None else defaults[param]

        # ------------------------------------------------------------
        # 处理保存格式
        # ------------------------------------------------------------
        if save_configs:
            for fmt, cfg in save_configs.items():
                # 从配置字典中弹出必要字段
                dir_name = cfg.pop('dir_name', None)
                file_name = cfg.pop('file_name', None)
                if dir_name is None or file_name is None:
                    raise ValueError(f"保存格式 {fmt} 的配置必须包含 'dir_name' 和 'file_name'")
                self.add_save(fmt, dir_name, file_name, **cfg)
        else:
            if config is not None:
                save_method = get_from_source(config, "save_method")
                if save_method is not None:
                    for file_format,save_config in asdict(save_method).items():
                        output_dir = save_config.pop("output_dir")
                        file_name = save_config.pop("file_name")
                        self.add_save(save_format=file_format, dir_name=output_dir, file_name=file_name,**save_config)
                        pass
                    pass
        # ------------------------------------------------------------
        # 判断模式是否改变（用于决定是否重建下载器）
        # ------------------------------------------------------------
        old_mode = self.config.mode
        mode_changed_by_param = mode is not None and mode != old_mode
        mode_changed_by_config = False
        if config is not None and hasattr(config, 'mode') and config.mode is not None:
            if config.mode != old_mode:
                mode_changed_by_config = True
        mode_changed = mode_changed_by_param or mode_changed_by_config

        # ------------------------------------------------------------
        # 更新配置（update_config=True 时写入 self.config）
        # ------------------------------------------------------------
        if update_config:
            # 顶层字段
            if group is not None:
                self.config.group = group
            if mode is not None:
                self.config.mode = mode
            if thread_count is not None:
                self.config.thread_count = thread_count
            # 浏览器配置
            if port is not None:
                self.config.browser.port = port
            if headless is not None:
                self.config.browser.headless = headless
            if user_data_dir is not None:
                self.config.browser.user_data_dir = user_data_dir
            if delay is not None and final_mode == DownloadMode.BROWSER:
                self.config.browser.delay = [float(delay[0]), float(delay[1])]
            if timeout is not None and final_mode == DownloadMode.BROWSER:
                self.config.browser.timeout = timeout
            if max_retry is not None and final_mode == DownloadMode.BROWSER:
                self.config.browser.max_retry = max_retry
            if interval is not None and final_mode == DownloadMode.BROWSER:
                self.config.browser.interval = float(interval)
            # API 配置
            if website is not None:
                if website not in self.config.api:
                    self.config.api[website] = SiteApiConfig()
                site_api = self.config.api[website]
                provider_name = api_name if api_name is not None else site_api.option
                if provider_name:
                    if provider_name not in site_api.providers:
                        site_api.providers[provider_name] = ApiProviderConfig()
                    provider = site_api.providers[provider_name]
                    if api_address is not None:
                        provider.address = api_address
                    if api_key is not None:
                        provider.key = api_key
                    if endpoint is not None:
                        provider.endpoint = endpoint
                    if params is not None:
                        provider.params = params
                    if delay is not None:
                        provider.delay = [float(delay[0]), float(delay[1])]
                    if timeout is not None:
                        provider.timeout = timeout
                    if max_retry is not None:
                        provider.max_retry = max_retry
                    if interval is not None:
                        provider.interval = float(interval)
                    if headers is not None:
                        provider.headers = headers
                    if api_name is not None:
                        provider.name = api_name
                if api_name is not None:
                    site_api.option = api_name
            # Requests 配置
            if website is not None:
                if website not in self.config.requests:
                    self.config.requests[website] = SiteRequestsConfig()
                site_req = self.config.requests[website]
                if cookies is not None:
                    site_req.cookies = cookies
                if headers is not None:
                    site_req.headers = headers
                if proxies is not None:
                    site_req.proxies = proxies
                if delay is not None:
                    site_req.delay = [float(delay[0]), float(delay[1])]
                if timeout is not None:
                    site_req.timeout = timeout
                if max_retry is not None:
                    site_req.max_retry = max_retry
                if interval is not None:
                    site_req.interval = float(interval)
            # 保存配置

            # 备份配置
            if backup_auto is not None:
                self.config.backup.auto = backup_auto
            if backup_interval is not None:
                self.config.backup.interval = backup_interval
            if backup_dir is not None:
                self.config.backup.backup_dir = backup_dir
            if backup_name is not None:
                self.config.backup.name = backup_name
            if backup_pop_up_folder is not None:
                self.config.backup.pop_up_folder = backup_pop_up_folder
            if backup_max_backups is not None:
                self.config.backup.max_backups = backup_max_backups

        # ------------------------------------------------------------
        # 将最终参数保存到运行时参数字典 _runtime_params
        # ------------------------------------------------------------
        self._runtime_params = final.copy()

        # ------------------------------------------------------------
        # 管理下载器列表
        # ------------------------------------------------------------

        target_count = final['thread_count']
        self.thread_count = target_count
        current_count = len(self.downloaders) if self.downloaders else 0

        if self.downloaders is None:
            self.downloaders = []

        # 核心修改：仅当允许创建且列表为空时才重建
        if create_if_missing and not self.downloaders:
            # 列表为空且允许创建：完全重新创建
            create_params = self.__build_create_params(final)
            downloaders_tuple = DownloaderFactory.create_downloader(**create_params)
            self.downloaders = list(downloaders_tuple)
        elif mode_changed and self.downloaders:
            # 模式变化且已有下载器：需要重建（无论是否允许创建，模式变化时必须重建）
            create_params = self.__build_create_params(final)
            downloaders_tuple = DownloaderFactory.create_downloader(**create_params)
            self.downloaders = list(downloaders_tuple)
        elif target_count != current_count and self.downloaders:
            # 线程数变化且已有下载器：追加或截断
            if target_count > current_count:
                needed = target_count - current_count
                create_params = self.__build_create_params(final, count=needed)
                new_downloaders_tuple = DownloaderFactory.create_downloader(**create_params)
                self.downloaders.extend(list(new_downloaders_tuple))
            else:
                self.downloaders = self.downloaders[:target_count]
            # 更新所有下载器属性
            self.__update_downloaders(self.downloaders, final)
        elif self.downloaders:
            # 已有下载器且无重大变化：仅更新属性
            self.__update_downloaders(self.downloaders, final)

        # ------------------------------------------------------------
        # 构建组信息字典（可选）
        # ------------------------------------------------------------
        self._group_dict = {
            "group_name": final['group'],
            "novel_name": None,
            "file_path": str(os.path.join("data", "Local", final["group"], "mems.json")),
            "url": None,
            "mode": final['mode'],
            "thread_count": final['thread_count'],
            "timeout": final['timeout'],
            "delay": final['delay'],
            "max_retry": final['max_retry'],
            "interval": final['interval'],
            "user_data_dir": final['user_data_dir'],
            "port": final['port'],
            "headless": final['headless'],
            "api_address": final['api_address'],
            "api_key": final['api_key'],
            "endpoint": final['endpoint'],
            "params": final['params'],
            "cookies": final['cookies'],
            "headers": final['headers'],
            "proxies": final['proxies'],
            "save_method":None,
        }
        pass

    @staticmethod
    def __build_create_params(final: dict, count: int = None) -> dict:
        """根据 final 字典构建传递给工厂的参数，可指定 count"""
        params = {
            'mode': final['mode'],
            'count': count if count is not None else final['thread_count'],
            'timeout': final.get('timeout'),
            'max_retry': final.get('max_retry'),
            'interval': final.get('interval'),
            'delay': final.get('delay'),
        }
        if final['mode'] == DownloadMode.BROWSER:
            params.update({
                'port': final.get('port'),
                'headless': final.get('headless'),
                'user_data_dir': final.get('user_data_dir'),
            })
        elif final['mode'] == DownloadMode.API:
            params.update({
                'address': final.get('api_address'),
                'api_key': final.get('api_key'),
                'endpoint': final.get('endpoint'),
                'params': final.get('params'),
            })
        elif final['mode'] == DownloadMode.REQUESTS:
            params.update({
                'cookies': final.get('cookies'),
                'headers': final.get('headers'),
                'proxies': final.get('proxies'),
            })
        return params

    @staticmethod
    def __update_downloaders(downloaders: list, final: dict):
        """用 final 中的参数更新下载器列表中的每个下载器"""
        for downloader in downloaders:
            # 通用属性
            if final.get('timeout') is not None:
                downloader.timeout = final['timeout']
            if final.get('max_retry') is not None:
                downloader.max_retry = final['max_retry']
            if final.get('interval') is not None:
                downloader.interval = final['interval']
            if final.get('delay') is not None:
                if hasattr(downloader, 'delay'):
                    downloader.delay = final['delay']
                elif hasattr(downloader, 'min_delay') and hasattr(downloader, 'max_delay'):
                    downloader.min_delay, downloader.max_delay = final['delay']
            # 模式特定属性
            if final['mode'] == DownloadMode.BROWSER:
                if final.get('port') is not None:
                    downloader.port = final['port']
                if final.get('headless') is not None:
                    downloader.headless = final['headless']
                if final.get('user_data_dir') is not None:
                    downloader.user_data_dir = final['user_data_dir']
            elif final['mode'] == DownloadMode.API:
                if final.get('api_address') is not None:
                    downloader.address = final['api_address']
                if final.get('api_key') is not None:
                    downloader.api_key = final['api_key']
                if final.get('endpoint') is not None:
                    downloader.endpoint = final['endpoint']
                if final.get('params') is not None:
                    downloader.params = final['params']
            elif final['mode'] == DownloadMode.REQUESTS:
                if final.get('cookies') is not None:
                    downloader.cookies = final['cookies']
                if final.get('headers') is not None:
                    downloader.headers = final['headers']
                if final.get('proxies') is not None:
                    downloader.proxies = final['proxies']
    def read_users_name(self):
        """读取所有用户名称"""
        return self.config_manager.read_users_name()
    def read_groups_name(self):
        return list(self.config.groups.groups.keys())
    def create_user(self, name):
        """创建用户"""
        if name == sanitize_name(name):
            self.config_manager.create_user(name)
            self.config = self.config_manager.config
            return True
        else:
            return False
    def create_group(self, name: str):
        """创建分组"""
        if name == sanitize_name(name):
            self.config.groups.create_group(name)
            self.save_config()
            return True
        else:
            return False
    def switch_user(self,name):
        """切换用户"""
        self.config_manager.load_config(name)
        self.config = self.config_manager.config
        self.save_config()
    def switch_group(self,name):
        """切换分组"""
        self.set(group=name,update_config=True,create_if_missing=False)
        self.save_config()
    def delete_user(self,name,deep=False):
        self.config_manager.delete_user(name,deep)
    def delete_group(self,name):
        self.config.groups.delete_group(name)

    def auto_backup(self):
        """备份"""
        if self.config.backup.auto:
            if time.time() - self.config.backup.last_time > self.config.backup.interval:
                novel_dir = dir_transform(self.config.backup.backup_dir,self.config.user,self.config.group,None)
                backup_path = os.path.join(self.config.backup.backup_dir,self.config.backup.name)
                import zipfile
                with zipfile.ZipFile(backup_path, 'w', self.config.backup.compression) as zipf:
                    for file in os.listdir(novel_dir):
                        if file.endswith(".json"):
                            zipf.write(os.path.join(novel_dir,file), file)
                self.config.backup.last_time = time.time()
        pass
