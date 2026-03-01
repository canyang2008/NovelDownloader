import os.path
from dataclasses import dataclass, field
from typing import Any
from novel_downloader.models import DownloadMode
from novel_downloader.models.backup import BackupConfig
from novel_downloader.models.group import Groups
from novel_downloader.models.save import SaveMethodConfig


@dataclass
class BrowserConfig:
    """浏览器通用配置"""
    timeout: int = 10
    max_retry: int = 3
    interval: float = 2.0
    delay: list[float] = field(default_factory=lambda: [3.0, 5.0])
    port: int = 9445
    headless: bool = False
    user_data_dir: str = os.path.join("data","Local","Default","User Data")


@dataclass
class ApiProviderConfig:
    """API提供商配置"""
    name: str = ""
    max_retry: int = 3
    timeout: int = 10
    interval: float = 2.0
    delay: list[float] = field(default_factory=lambda: [3.0, 5.0])
    key: str = ""
    endpoint: str = ""
    address: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    # 其他提供商特定字段
    extra_params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True  # 是否启用


@dataclass
class SiteApiConfig:
    """网站API配置"""
    option: str = ""  # 当前选择的API
    providers: dict[str, ApiProviderConfig] = field(default_factory=dict)

    def get_provider(self,option=None) -> ApiProviderConfig | None:
        """获取API提供商，默认激活的API提供商"""
        if not option:
            option=self.option
        if option and option in self.providers:
            return self.providers[option]
        return None


@dataclass
class SiteRequestsConfig:
    """网站Requests配置"""
    max_retry: int = 3
    timeout: int = 10
    interval: float = 2.0
    delay: list[float] = field(default_factory=lambda: [3.0, 5.0])
    cookies: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    proxies: dict[str, str] = field(default_factory=dict)


@dataclass
class UserConfig:
    """用户特定配置"""
    version: str = "1.1.0"
    user: str = "Default"
    group: str = "Default"
    readme: str = ""
    play_sound: dict[str,bool] = field(default_factory=lambda: {"completion":False})
    mode: DownloadMode = DownloadMode.BROWSER  # 0=Browser, 1=API, 2=Requests

    # 线程配置
    thread_count: int = 3

    # 下载配置
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    api: dict[str, SiteApiConfig] = field(default_factory=dict)  # 网站 -> API配置
    requests: dict[str, SiteRequestsConfig] = field(default_factory=dict)

    # 组配置
    groups:Groups = field(default_factory=Groups)

    # 保存配置
    save_method: SaveMethodConfig = field(default_factory=SaveMethodConfig)

    # 备份配置
    backup: BackupConfig = field(default_factory=BackupConfig)

    # 未处理项目（用于扩展）
    unprocess: list[Any] = field(default_factory=list)
