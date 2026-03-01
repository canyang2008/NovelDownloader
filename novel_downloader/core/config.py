import base64
import copy
import json
import os
from typing import Any
from novel_downloader import UserConfig, DownloadMode, BaseSaveConfig
from novel_downloader.models.save import ImgSaveConfig, EpubSaveConfig, JsonSaveConfig, TxtSaveConfig, HtmlSaveConfig

from novel_downloader.outputs import dir_transform
from novel_downloader.models.group import Group, Groups
from novel_downloader.models.config import (
    DownloadMode,
    BrowserConfig,
    SiteApiConfig,
    SiteRequestsConfig,
    ApiProviderConfig,
    SaveMethodConfig,
    BackupConfig
)
class ConfigManager1:
    """配置管理器"""

    def __init__(self):
        self.__base_dir = None
        self.__user = "Default"
        self.__user_data_dir = None
        from novel_downloader.models.config import UserConfig
        self.config = UserConfig()
        self.load_config()

    def load_config(self,user:str=None):
        """加载配置文件"""
        with open(os.path.join("data","Local","manage.json"), "r", encoding="utf-8") as f:
            all_user_config = json.load(f)
        """解析当前用户数据"""
        if not user:
            self.__user = all_user_config.get("USER")
        else:self.__user = user
        user_config = all_user_config["USERS"].get(self.__user)
        self.__user_data_dir = user_config.get("User_data_dir")
        self.__base_dir = user_config.get("Base_dir")
        group_file = os.path.join(self.__base_dir, "mems.json")
        config_file = user_config.get("User_config_path")
        self._parse_config(config_file)
        self.parse_group(group_file)

    def _parse_config(self, config_file:str):
        """解析原始配置数据"""
        with open(config_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        # 基础字段
        self.config.version = raw_data.get("Version")
        self.config.group = raw_data.get("Group")
        self.config.readme = raw_data.get("README")
        self.config.play_sound = {"completion":raw_data.get("Play_completion_sound")}
        self.config.mode = raw_data.get("Get_mode")
        self.config.thread_count = raw_data.get("Threads_num")
        mode = raw_data.get("Get_mode")
        if mode == 0:
            self.config.mode = DownloadMode.BROWSER
        elif mode == 1:
            self.config.mode = DownloadMode.API
        elif mode == 2:
            self.config.mode = DownloadMode.REQUESTS
        else:
            self.config.mode = DownloadMode.BROWSER

        # 浏览器配置
        browser_data = raw_data.get("Browser")

        self.config.browser = BrowserConfig(
            timeout=browser_data.get("Timeout"),
            max_retry=browser_data.get("Max_retry"),
            interval=browser_data.get("Interval"),
            delay=browser_data.get("Delay"),
            port=browser_data.get("Port"),
            headless=browser_data.get("Headless"),
            user_data_dir=self.__user_data_dir,  # 使用用户特定的数据目录
        )

        # API配置
        api_data = raw_data.get("Api")
        for site, site_config in api_data.items():
            site = site.lower()
            option = site_config.get("Option")
            providers = {}

            # 解析每个API配置
            for provider_name, provider_config in site_config.items():
                if provider_name != "Option":
                    provider_name = provider_name.lower()
                    providers[provider_name] = ApiProviderConfig(
                        name=provider_name,
                        max_retry=provider_config.get("Max_retry"),
                        timeout=provider_config.get("Timeout"),
                        interval=provider_config.get("Interval"),
                        delay=provider_config.get("Delay"),
                        key=provider_config.get("Key"),
                        endpoint=provider_config.get("Endpoint"),
                        headers=provider_config.get("Headers"),
                        params=provider_config.get("Params"),
                        enabled=provider_config.get("Enabled")
                    )

            self.config.api[site] = SiteApiConfig(option=option, providers=providers)

        # Requests配置
        requests_data = raw_data.get("Requests")
        for site, site_config in requests_data.items():
            site = site.lower()
            self.config.requests[site] = SiteRequestsConfig(
                max_retry=site_config.get("Max_retry"),
                timeout=site_config.get("Timeout"),
                interval=site_config.get("Interval"),
                delay=site_config.get("Delay"),
                cookies=site_config.get("Cookie"),
                headers=site_config.get("Headers"),
                proxies=site_config.get("Proxies")
            )

        # 保存方法配置
        save_data = raw_data.get("Save_method")
        from novel_downloader.models.save import JsonSaveConfig, TxtSaveConfig, HtmlSaveConfig, BaseSaveConfig
        json_save_config = save_data.get("json")
        json_save_config = JsonSaveConfig(
            enable=json_save_config.get("enable",True),
            file_name=json_save_config.get("name") if json_save_config.get("name")!="name_default" else None,
            output_dir=json_save_config.get("dir"),
            indent=json_save_config.get("indent",4),
            save_interval=json_save_config.get("interval",3),
            ensure_ascii=json_save_config.get("ensure_ascii",False),
            extension=json_save_config.get("extension",".json"),
        )
        img_save_config = ImgSaveConfig(
            output_dir=save_data.get("json",{}).get("img_dir"),
            file_name=None,
        )

        txt_save_config = save_data.get("txt")
        txt_save_config = TxtSaveConfig(
            enable=txt_save_config.get("enable"),
            file_name=txt_save_config.get("name") if txt_save_config.get("name")!="name_default" else None,
            output_dir=txt_save_config.get("dir"),
            chapters_per_file=txt_save_config.get("gap"),
            file_size=txt_save_config.get("max_filesize", -1),
            encoding=txt_save_config.get("encoding","utf-8"),
            extension=txt_save_config.get("extension",".txt"),
        )

        html_save_config = save_data.get("html")
        html_save_config = HtmlSaveConfig(
            enable=html_save_config.get("enable"),
            file_name=html_save_config.get("name") if html_save_config.get("name")!="name_default" else None,
            output_dir=html_save_config.get("dir"),
            one_file=html_save_config.get("one_file",True),
            template=html_save_config.get("template","default"),
            extension=html_save_config.get("extension",".html")
        )

        epub_save_config = save_data.get("epub",{})
        epub_save_config = EpubSaveConfig(
            enable=epub_save_config.get("enable",False),
            file_name=epub_save_config.get("name") if epub_save_config.get("name")!="name_default" else None,
            extension=epub_save_config.get("extension",".epub"),
        )

        self.config.save_method = SaveMethodConfig(
            base=BaseSaveConfig(output_dir=self.__base_dir),
            json=json_save_config,
            txt=txt_save_config,
            html=html_save_config,
            img=img_save_config,
            epub=epub_save_config,
        )
        # 备份配置
        backup_data = raw_data.get("Backup")
        self.config.backup = BackupConfig(
            auto=backup_data.get("Auto"),
            interval=int(backup_data.get("Auto_save_method")[2:]),
            backup_dir=backup_data.get("Dir"),
            name=backup_data.get("Name"),
            last_time=backup_data.get("Last_time"),
            compression=backup_data.get("Compression",0),
        )
        # 未处理项目
        self.config.unprocess = raw_data.get("Unprocess")

    def parse_group(self, group_file=None):
        """解析分组配置数据"""
        if group_file is None:
            group_file = os.path.join("data", "Local", self.__user, "json", "mems.json")
        group_dir = dir_transform(os.path.dirname(group_file),None,None,None)
        with open(group_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        groups = Groups(version=None)
        for group_name, value in raw_data.items():
            if group_name == "Version":
                groups = Groups(version=value)
            else:
                for novel_name,url in value.items():
                    group_path = str(os.path.join(group_dir, novel_name+".json"))
                    group = Group(group_name=group_name,url=url,novel_name=novel_name,file_path=group_path)
                    groups.update(group)
        self.config.groups = groups
        pass
    def save_config(self):
        # 转换 Get_mode
        user_config = self.config
        mode_int = 0
        if user_config.mode == DownloadMode.BROWSER:
            mode_int = 0
        elif user_config.mode == DownloadMode.API:
            mode_int = 1
        elif user_config.mode == DownloadMode.REQUESTS:
            mode_int = 2

        # 构建输出字典
        config_dict:dict[str,Any] = {
            "Version": user_config.version,
            "User_name": user_config.user,
            "Group": user_config.group,
            "README": user_config.readme,
            "Threads_num": user_config.thread_count,
            "Play_completion_sound": user_config.play_sound.get("completion", True),
            "Get_mode": mode_int,
            "Browser": {
                "Timeout": user_config.browser.timeout,
                "Max_retry": user_config.browser.max_retry,
                "Interval": user_config.browser.interval,
                "Delay": user_config.browser.delay,
                "Port": user_config.browser.port,
                "Headless": user_config.browser.headless,
                "path": user_config.browser.user_data_dir
            },
            "Api": {},
            "Requests": {},
            "Save_method": {},
            "Backup": {
                "Auto": user_config.backup.auto,
                "Auto_save_method": f"T:{user_config.backup.interval}",
                "Dir": user_config.backup.backup_dir,
                "Name": user_config.backup.name,
                "Last_time": user_config.backup.last_time,
                "Pop_up_folder": user_config.backup.pop_up_folder
            },
            "Unprocess": user_config.unprocess
        }

        # 处理 Api
        for site_name, site_api in user_config.api.items():
            site_key = site_name.capitalize()
            provider = site_api.get_provider()
            if provider is None:
                continue
            config_dict["Api"][site_key] = {
                "Option": site_api.option,
                site_api.option: {
                    "Max_retry": provider.max_retry,
                    "Timeout": provider.timeout,
                    "Interval": provider.interval,
                    "Delay": provider.delay,
                    "Key": provider.key
                }
            }

        # 处理 Requests
        for site_name, site_req in user_config.requests.items():
            site_key = site_name.capitalize()
            config_dict["Requests"][site_key] = {
                "Max_retry": site_req.max_retry,
                "Timeout": site_req.timeout,
                "Interval": site_req.interval,
                "Delay": site_req.delay,
                "Cookie": site_req.cookies
            }

        save = user_config.save_method

        if save.json:
            json_entry = {
                "enable": save.json.enable,
                "name": save.json.file_name if save.json.file_name is not None else "name_default",
                "dir": save.json.output_dir,
                "img_dir": save.img.output_dir if save.img else "data\\Bookstore\\<User>\\<Group>\\<Name>\\Img"
            }
            config_dict["Save_method"]["json"] = json_entry

        if save.txt:
            txt_entry = {
                "enable": save.txt.enable,
                "name": save.txt.file_name if save.txt.file_name is not None else "name_default",
                "dir": save.txt.output_dir,
                "gap": save.txt.chapters_per_file,
                "max_filesize": save.txt.file_size
            }
            config_dict["Save_method"]["txt"] = txt_entry

        if save.html:
            html_entry = {
                "enable": save.html.enable,
                "name": save.html.file_name if save.html.file_name is not None else "name_default",
                "dir": save.html.output_dir,
                "one_file": save.html.one_file
            }
            config_dict["Save_method"]["html"] = html_entry
        with open(os.path.join("data","Local",user_config.group,"UserConfig.json"),"w",encoding="utf-8") as f:
            json.dump(config_dict,f,ensure_ascii=False,indent=4)

        groups_dict:dict[str,str|dict[str,str]] = {
            "Version": user_config.groups.version if user_config.groups.version is not None else "1.1.0"
        }

        for group_name, group_tuple in user_config.groups.groups.items():
            novels_dict = {}
            for group in group_tuple:
                novels_dict[group.novel_name] = group.url
            groups_dict[group_name] = novels_dict

        with open(os.path.join("data","Local",user_config.group,"json","mems.json"),"w",encoding="utf-8") as f:
            f.write(json.dumps(groups_dict,ensure_ascii=False,indent=4))
    @staticmethod
    def read_users_name():
        with open(os.path.join("data","Local","manage.json"), "r", encoding="utf-8") as f:
            all_user_config = json.load(f)
        result = list(all_user_config["USERS"].keys())
        return result
    @staticmethod
    def create_user(name):
        from novel_downloader.utils.init_config import init1
        init1(name)
    def delete_user(self,name,deep=False):
        with open(os.path.join("data","Local","manage.json"), "r", encoding="utf-8") as f:
            all_user_config = json.load(f)
        all_user_config["USERS"].pop(name)
        with open(os.path.join("data","Local","manage.json"), "w", encoding="utf-8") as f:
            json.dump(all_user_config, f, ensure_ascii=False, indent=4)
        self.load_config()
        if deep:
            os.remove(os.path.join("data","Local",name))

class ConfigManager2:
    def __init__(self):
        self.__user = None
        from novel_downloader.models.config import UserConfig
        self.config = UserConfig()
        self.load_config()
    def load_config(self,user:str=None):
        with open(os.path.join("data","Local","SettingConfig.json"),"r",encoding="utf-8") as f:
            all_user_config = json.load(f)
        if not user:
            self.__user = all_user_config.get("USER")
        else:self.__user = user
        self._parse_config(all_user_config[self.__user])
        self.parse_group()
    def _parse_config(self,user_config):
        """解析原始配置数据"""
        raw_data = user_config
        # 基础字段
        self.config = UserConfig(**user_config)
        self.config.browser = BrowserConfig(**user_config["browser"])
        self.config.api = {
            "fanqie": SiteApiConfig(**user_config["api"]["fanqie"]),
            "qidian": SiteApiConfig(**user_config["api"]["qidian"]),
        }
        self.config.requests = {
            "fanqie": SiteRequestsConfig(**user_config["requests"]["fanqie"]),
            "qidian": SiteRequestsConfig(**user_config["requests"]["qidian"]),
            "biquge": SiteRequestsConfig(**user_config["requests"]["biquge"]),
        }
        self.config.backup = BackupConfig(**user_config["backup"])
        save_method_dict = raw_data.pop("save_method")
        save_method = SaveMethodConfig()
        for file_format,save_config in save_method_dict.items():
            if file_format != "base":
                setattr(save_method,file_format,save_config)
        self.config.save_method = SaveMethodConfig()

        if self.config.mode == 0:
            self.config.mode = DownloadMode.BROWSER
        elif self.config.mode == 1:
            self.config.mode = DownloadMode.API
        elif self.config.mode == 2:
            self.config.mode = DownloadMode.REQUESTS
        else:
            self.config.mode = DownloadMode.BROWSER
        pass
    def parse_group(self):
        with open(os.path.join("data","Local","UrlConfig.json"),encoding="utf-8") as f:
            json_data = json.load(f)
        groups = Groups(version=json_data["version"])
        for group_name,groups_dict in json_data["groups"].items():

            for group_dict in groups_dict:
                group = Group(**group_dict)
                save_method = {
                    "base": BaseSaveConfig(**group_dict["save_method"].get("base",{})),
                    "json": JsonSaveConfig(**group_dict["save_method"].get("json",{})),
                    "txt": TxtSaveConfig(**group_dict["save_method"].get("txt",{})),
                    "epub": EpubSaveConfig(**group_dict["save_method"].get("epub",{})),
                    "html": HtmlSaveConfig(**group_dict["save_method"].get("html",{})),
                    "img": ImgSaveConfig(**group_dict["save_method"].get("img",{})),
                }
                group.save_method = SaveMethodConfig(**save_method)
                groups.update(group)
        self.config.groups = groups
        for name,groups in self.config.groups.groups.items():
            for group in groups:
                mode_int = group.mode
                if mode_int == 0:
                    group.mode = DownloadMode.BROWSER
                elif mode_int == 1:
                    group.mode = DownloadMode.API
                elif mode_int == 2:
                    group.mode = DownloadMode.REQUESTS
                else:
                    group.mode = DownloadMode.BROWSER
    def save_config(self):
        user_config = self.config
        mode_int = 0
        if user_config.mode == DownloadMode.BROWSER:
            mode_int = 0
        elif user_config.mode == DownloadMode.API:
            mode_int = 1
        elif user_config.mode == DownloadMode.REQUESTS:
            mode_int = 2

        from dataclasses import asdict
        user_config_dict:dict[str,Any] = asdict(user_config)
        user_config_dict.pop("groups")
        user_config_dict["mode"] = mode_int
        with open(os.path.join("data","Local","SettingConfig.json"),"r",encoding="utf-8") as f:
            all_user_config = json.load(f)
        all_user_config[self.config.user] = user_config_dict
        with open(os.path.join("data","Local","SettingConfig.json"),"w",encoding="utf-8") as f:
            json.dump(all_user_config,f,ensure_ascii=False,indent=4)

        groups_dict = asdict(self.config.groups)
        for k,groups in groups_dict["groups"].items():
            if groups:
                for group in groups:
                    if group["mode"] == DownloadMode.BROWSER:
                        group["mode"] = 0
                    elif group["mode"] == DownloadMode.API:
                        group["mode"] = 1
                    elif group["mode"] == DownloadMode.REQUESTS:
                        group["mode"] = 2
        with open(os.path.join("data","Local","UrlConfig.json"),"w",encoding="utf-8") as f:
            json.dump(groups_dict,f,ensure_ascii=False,indent=4)
    @staticmethod
    def read_users_name():
        with open(os.path.join("data","Local","SettingConfig.json"),"r",encoding="utf-8") as f:
            json_data = json.load(f)
            result = list(json_data.keys())[2:]
            return result
    @staticmethod
    def create_user(name):
        from novel_downloader.utils.init_config import init2
        init2(name)
    def delete_user(self,name,deep=False):
        with open(os.path.join("data","Local","SettingConfig.json"), "r", encoding="utf-8") as f:
            all_user_config = json.load(f)
        all_user_config.pop(name)
        with open(os.path.join("data","Local","SettingConfig.json"), "w", encoding="utf-8") as f:
            json.dump(all_user_config, f, ensure_ascii=False, indent=4)
        self.load_config()
        if deep:
            os.remove(os.path.join("data","Local",name))
