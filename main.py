import argparse
import platform
import re
import subprocess
import time
from tqdm import tqdm
from dataclasses import dataclass
from novel_downloader import NovelDownloader, parse_url, Chapter
from novel_downloader.models import Website, DownloadMode
from novel_downloader.models.group import Group
from novel_downloader.parsers import FeatureNotSupportedError
@dataclass
class Options:
    url:str = None
    not_update:bool = None
    title_key:str = None
    ranges:str = None
    mode:int = None
    delay:list[float]|str = None
    threads:int = None
    timeout:int = None
    max_retry:int = None
    interval:int = None
    user_data_dir:str = None
    port:int = None
    group:str = None
    headless:bool = False
    api_key:str = None
    cookies:str = None
    save_format:str = None
    save_file_path:str = None
    dry_run:str = None
import os
from colorama import Fore, init
from novel_downloader.utils.init_config import init1, init2
init(autoreset=True)
def check():
    # 格式化
    config_method = 2
    if not os.path.exists(os.path.join("data", "Local")):
        init_choice = init2
        os.makedirs(os.path.join("data", "Local"))
        file = open(os.path.join("data", "Local","config_method.txt"), "w")
        while True:
            choice = input("请选择配置方式：\n1.分散型\n2.集合型").strip()
            if choice == "1":
                init_choice = init1
                file.write("1")
                config_method = 1
                break
            elif choice == "2":
                init_choice = init2
                config_method = 2
                file.write("2")
                break
            else:
                print("选择错误，请重新选择")
                continue
        print(f"{Fore.YELLOW}重置中")
        init_choice()
        print(f"{Fore.GREEN}重置成功")
        file.close()
        return config_method
    else:
        with open(os.path.join("data", "Local","config_method.txt"), "r") as f:
            config_method = int(f.read())
        return config_method

def range_split(deal_range, total_list) -> tuple | list | None:
    """
    处理范围字符串，将其转换为索引列表。
    """
    if deal_range is None:
        return None
    # 处理特殊关键字
    if deal_range.lower() == "all":
        return list(range(1, total_list + 1))

    if deal_range.lower().startswith("last:"):
        try:
            count = int(deal_range.split(":")[1])
            return list(range(max(1, total_list - count + 1), total_list + 1))
        except (ValueError, IndexError):
            pass  # 格式错误时按普通方式处理

    # 分割范围表达式
    segments = re.split(r'[\s,;、；]+', deal_range.strip())
    result_range = set()

    for seg in segments:
        if not seg:
            continue

        # 处理范围格式 (如 5-8)
        if '-' in seg:
            parts = seg.split('-')
            if len(parts) == 2:
                try:
                    start = int(parts[0]) if parts[0] else 1
                    end = int(parts[1]) if parts[1] else total_list

                    # 确保范围有效
                    start = max(1, min(start, total_list))
                    end = max(1, min(end, total_list))

                    # 添加范围内
                    if start <= end:
                        result_range.update(range(start, end + 1))
                except ValueError:
                    continue
            # 处理开区间 (如 -5 或 5-)
            elif len(parts) == 1:
                if seg.startswith('-'):
                    try:
                        end = int(parts[0])
                        result_range.update(range(1, min(end, total_list) + 1))
                    except ValueError:
                        continue
                elif seg.endswith('-'):
                    try:
                        start = int(parts[0])
                        result_range.update(range(max(1, start), total_list + 1))
                    except ValueError:
                        continue

        # 处理单个范围
        else:
            try:
                single_range = int(seg)
                if 1 <= single_range <= total_list:
                    result_range.add(single_range)
            except ValueError:
                continue

    # 转换为有序列表
    sorted_range = tuple(sorted(result_range))

    return sorted_range

parser = argparse.ArgumentParser()
parser.add_argument("--url",type=str)
parser.add_argument("--dry-run",action="store_true")
parser.add_argument("--group",type=str)
parser.add_argument("--title-key",type=str)
parser.add_argument("--not-update",type=bool)
parser.add_argument("--threads",type=int)
parser.add_argument("--range", type=str)
parser.add_argument("--mode",type=int)
parser.add_argument("--delay",type=str)
parser.add_argument("--timeout",type=int)
parser.add_argument("--data-dir",type=str)
parser.add_argument("--max-retry",type=int)
parser.add_argument("--interval",type=int)
parser.add_argument("-p","--port",type=int)
parser.add_argument("--headless",action="store_true")
parser.add_argument("--api-key",type=str)
parser.add_argument("--cookies",type=str)
parser.add_argument("--save-format",type=str)
parser.add_argument("--save-file-path",type=str)


class ND(NovelDownloader):
    def __init__(self,config_option=1):
        super().__init__(config_option)
        self.options = None
        self._saved_config = None

    def parse_args(self):
        args = parser.parse_args()
        self.options = Options()
        self.options.url = args.url
        self.options.not_update = args.not_update
        self.options.title_key = args.title_key
        self.options.ranges = args.range
        self.options.mode = args.mode
        self.options.threads = args.threads
        self.options.delay = args.delay
        self.options.timeout = args.timeout
        self.options.max_retry = args.max_retry
        self.options.interval = args.interval
        self.options.user_data_dir = args.data_dir
        self.options.port = args.port
        self.options.group = args.group
        self.options.headless = args.headless
        self.options.api_key = args.api_key
        self.options.cookies = args.cookies
        self.options.save_format = args.save_format
        self.options.save_file_path = args.save_file_path
        if self.options.delay and len(self.options.delay.split("-")) == 2:
            self.options.delay = [float(self.options.delay.split("-")[0]),float(self.options.delay.split("-")[1])]
        pass

    def __download(self, download_url, orders):
        orders.sort()
        self._saved_config = False
        download_progress = tqdm(orders,desc=self.novel.name)
        split_index = 0
        download_orders_list = []
        batch_size = nd.parser.batch_size
        while True:             # 分配任务
            download_orders_list.append(orders[split_index:split_index + batch_size])
            split_index += batch_size
            if split_index >= len(orders):break
        from concurrent.futures import ThreadPoolExecutor, as_completed
        thread_count = self.thread_count
        with ThreadPoolExecutor(max_workers=self.thread_count) as executor:
            # 创建任务列表
            tasks = []
            thread_index = -1
            for download_orders in download_orders_list:
                thread_index+=1
                index = thread_index % self.thread_count
                tasks.append(executor.submit(
                    self.get_chapters,
                    download_url=download_url,
                    orders=download_orders,
                    choice=index,
                ))
                if len(tasks) == thread_count:
                    chapters_list:list[Chapter|None] = []
                    for future in as_completed(tasks):
                        chapters = future.result()
                        chapters_list.extend(chapters)
                    else:
                        if any(isinstance(item, Chapter) for item in chapters_list):
                            chapters_list.sort(key=lambda x:x.order)
                            if self._saved_config is not None and not self._saved_config:
                                self.config.groups.update(self.novel.group)
                                self.save_config()
                                self._saved_config = True
                            self.save_novel(chapters=chapters_list)
                            if None in chapters_list:
                                update_index = chapters_list.index(None)
                                download_progress.update(update_index)
                            else:
                                update_index = len(chapters_list)
                                download_progress.update(update_index)
                        else:
                            download_progress.close()
                            break

                    tasks = []

            # 处理完成的任务
    def cli_download_novel(self):
        self.parse_args()
        download_url = self.options.url
        url,website = parse_url(download_url)
        self.set(**self.options,website = website)
        novel = self.get_info(url=download_url)
        if self.options.ranges:
            total_chapters = novel.total
            if total_chapters:
                download_range = range_split(self.options.ranges, total_chapters)
            else:
                download_range = range_split(self.options.ranges,25001)
            file_name_default = novel.name+self.options.ranges
        else:
            if len(novel.chapters) == 0:
                download_range = tuple(range(1,25001))
            else:download_range = tuple(range(len(novel.chapters)))
            file_name_default = novel.name
        if self.options.save_format in ["json", "txt", "html"]:
            if self.options.save_file_path:
                file_name = os.path.basename(self.options.save_file_path)
                dir_name = os.path.dirname(self.options.save_file_path)
            else:
                save_config = getattr(self.config.save_method,self.options.save_format)
                dir_name = save_config.dir_name
                file_name = save_config.file_name
            self.add_save(self.options.save_format, dir_name=dir_name, file_name=file_name)
        else:
            from dataclasses import fields, asdict
            for save_config_field in fields(self.config.save_method):
                if save_config_field.name == "base" and self.options.dry_run:
                    continue
                save_config = getattr(save_config_field, save_config_field.name)
                file_name = save_config.file_name
                if file_name == "name_default":
                    file_name = file_name_default
                save_config = asdict(save_config)
                save_config["file_name"] = file_name
                self.add_save(save_config_field.name,**save_config)
        self.__download(download_url=download_url, orders=download_range)

    def search(self):
        choice = input("""请选择网站：
        1.番茄：
        2.起点：
        ：""").strip()
        if choice == "1":
            search_website = Website.FANQIE
        elif choice == "2":
            search_website = Website.QIDIAN
        else:
            print("清输入正确的数字")
            return None
        search_key = input("请输入关键词：").strip()
        if search_key:
            try:
                self.set(config=self.config, website=search_website)
                search_result = self.search_novel(website=search_website, search_key=search_key)
                search_index = 0
                for novel_info in search_result:
                    search_index+=1
                    print(f"{search_index}.小说名：{novel_info['name']}  作者：{novel_info['author']}  url:{novel_info.get('url','无')}")
                choice = input("\n请选择：").strip()
                choice = int(choice)
                book_url = self.search_novel(website=search_website, search_key=search_key, download_choice=choice-1)
                self.download_novel(book_url)
            except FeatureNotSupportedError as e:
                print(e)
                return None
        else:
            print("清输入正确的关键词")
            return None

    def setting(self):
        """配置菜单"""
        import json
        while True:
            option = input(
"""
请输入数字
1.账户
2.分组
3.参数修改
输入q退出："""
).strip()
            if option == "q":
                return None
            elif option == "1":
                while True:
                    choice = input("1.账户切换    2.账户创建    3.账户删除\n输入q退出：").strip()
                    if choice == "q":
                        break
                    elif choice == "1":
                        users_list = self.read_users_name()
                        while True:
                            user_index = 0
                            print("请选择账户\n")
                            for user in users_list:
                                print(f"{user_index+1}.{user}")
                                user_index+=1
                            choice_user_index_str = input().strip()
                            if choice_user_index_str == "q":
                                break
                            else:
                                try:
                                    choice_user_index = int(choice_user_index_str)
                                    if choice_user_index>len(users_list):
                                        print("选择错误")
                                        continue
                                    else:
                                        self.switch_user(users_list[choice_user_index-1])
                                        print(f"切换成功({self.config.user})")
                                        return None
                                except ValueError:
                                    print("输入错误，必须输入纯数字")
                                    continue
                    elif choice == "2":
                        while True:
                            user_str = input("请输入账户名")
                            if self.create_user(user_str):
                                print("创建成功")
                                choice = input("是否切换(y/n)")
                                if choice == "y":
                                    self.switch_user(user_str)
                                    print(f"切换成功({self.config.user})")
                                    return None
                                else:break
                            else:
                                print("名称非法，请重新输入")
                                continue
                    elif choice == "3":
                        users_list = self.read_users_name()
                        while True:
                            user_index = 0
                            print("请选择账户\n")
                            for user in users_list:
                                print(f"{user_index}.{user}")
                                user_index+=1
                            choice_user_index_str = input().strip()
                            if choice_user_index_str == "q":
                                break
                            else:
                                try:
                                    choice_user_index = int(choice_user_index_str)
                                    if choice_user_index>len(users_list):
                                        print("选择错误")
                                        continue
                                    else:
                                        if self.config.user == users_list[choice_user_index-1]:
                                            print("不可删除当前用户")
                                            return None
                                        choice = input("是否彻底删除(y/n)")
                                        if choice == "y":
                                            self.delete_user(users_list[choice_user_index-1],deep=True)
                                            print("删除成功")
                                            return None
                                        else:
                                            self.delete_user(users_list[choice_user_index-1],deep=False)
                                        break
                                except ValueError:
                                    print("输入错误，必须输入纯数字")
                                    continue

            elif option == "2":
                while True:
                    choice = input("1.分组切换    2.分组创建    3.分组删除\n").strip()
                    if choice == "q":
                        break
                    elif choice == "1":
                        groups_list = self.read_groups_name()
                        if not groups_list:
                            print("无分组")
                        while True:
                            print("请选择分组\n")
                            for idx,group in enumerate(groups_list,start=1):
                                print(f"{idx}.{group}")
                            choice_group_index_str = input().strip()
                            if choice_group_index_str == "q":
                                break
                            else:
                                try:
                                    choice_user_index = int(choice_group_index_str)
                                    if choice_user_index>len(groups_list) or choice_user_index<=0:
                                        print("选择错误")
                                        continue
                                    else:
                                        self.switch_group(groups_list[choice_user_index-1])
                                        print(f"切换成功({self.config.group})")
                                        return None
                                except ValueError:
                                    print("输入错误，必须输入纯数字")
                                    continue
                    elif choice == "2":
                        while True:
                            group_str = input("请输入分组名")
                            if self.create_group(group_str):
                                print(f"创建成功({self.config.group})")
                                choice = input("是否切换(y/n)")
                                if choice == "y":
                                    self.switch_group(group_str)
                                    print(f"切换成功({self.config.group})")
                                return None
                            else:
                                print("名称非法，请重新输入")
                                continue
                    elif choice == "3":
                        groups_list = self.read_groups_name()
                        if not groups_list:
                            print("无分组")
                            return None
                        while True:
                            print("请选择分组\n")
                            for idx,group in enumerate(groups_list,start=1):
                                print(f"{idx}.{group}")
                            choice_group_index_str = input().strip()
                            if choice_group_index_str == "q":
                                break
                            else:
                                try:
                                    choice_group_index = int(choice_group_index_str)
                                    if choice_group_index>len(groups_list):
                                        print("选择错误")
                                        continue
                                    else:
                                        if self.config.group == groups_list[choice_group_index-1]:
                                            print("不可删除当前分组")
                                            break
                                        return None
                                except ValueError:
                                    print("输入错误，必须输入纯数字")
                                    continue

                pass
            elif option == "3":
                while True:
                    print("""
1.获取模式
2.Chrome设置
3.API设置
4.Requests设置
6.备份设置
其他请在相关配置修改
输入q退出：""")
                    option = input().strip()
                    if option == "q":
                        return None

                    # 1. 获取模式设置
                    if option == "1":
                        while True:
                            mode_option = input("""
1.Chrome模式
2.API模式
3.Requests模式
输入q退出:""").strip()
                            if mode_option == "q":
                                break
                            elif mode_option == "1":
                                self.set(config=self.config, mode=DownloadMode.BROWSER, update_config=True, create_if_missing=False)
                                self.save_config()
                                break
                            elif mode_option == "2":
                                self.set(config=self.config, mode=DownloadMode.API, update_config=True, create_if_missing=False)
                                self.save_config()
                                break
                            elif mode_option == "3":
                                self.set(config=self.config, mode=DownloadMode.REQUESTS, update_config=True, create_if_missing=False)
                                self.save_config()
                                break
                            else:
                                print("请重新输入\n")
                                continue

                    # 2. Chrome设置
                    elif option == "2":
                        while True:
                            print(f'''
1.超时时间(当前:{self.config.browser.timeout}s)
2.最大重试次数(当前:{self.config.browser.max_retry}次)
3.重试时间间隔(当前:{self.config.browser.interval}s)
4.延迟(当前:{'s '.join(str(x) for x in self.config.browser.delay)})
5.端口号(当前:{self.config.browser.port})
6.无头模式(当前:{self.config.browser.headless})
7.用户数据目录(当前:{self.config.browser.user_data_dir})
输入q退出:''')
                            choice = input().strip()
                            if choice == "q":
                                break
                            elif choice == "1":
                                while True:
                                    para_str = input("请输入:").strip()
                                    if para_str == "q":
                                        break
                                    try:
                                        self.set(config=None, mode=DownloadMode.BROWSER, timeout=int(para_str),
                                                 update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "2":
                                while True:
                                    para_str = input("请输入:").strip()
                                    if para_str == "q":
                                        break
                                    try:
                                        self.set(config=None, mode=DownloadMode.BROWSER, max_retry=int(para_str),
                                                 update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "3":
                                while True:
                                    para_str = input("请输入:").strip()
                                    if para_str == "q":
                                        break
                                    try:
                                        self.set(config=None, mode=DownloadMode.BROWSER, interval=float(para_str),
                                                 update_config=True)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "4":
                                while True:
                                    para_str = input("请输入上限 下限，用空格隔开").strip()
                                    if para_str == "q":
                                        break
                                    dalay = para_str.split()
                                    try:
                                        self.set(config=None, mode=DownloadMode.BROWSER,
                                                 delay=[float(dalay[0]), float(dalay[1])],
                                                 update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                                    except IndexError:
                                        print("未输入上|下限，请重新输入")
                            elif choice == "5":
                                while True:
                                    para_str = input("请输入:").strip()
                                    if para_str == "q":
                                        break
                                    try:
                                        self.set(config=None, mode=DownloadMode.BROWSER, port=int(para_str),
                                                 update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "6":
                                while True:
                                    para_str = input("是否无头(y|n):").strip()
                                    if para_str == "q":
                                        break
                                    elif para_str == "y":
                                        self.set(mode=DownloadMode.BROWSER, headless=True,
                                                 update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    elif para_str == "n":
                                        self.set(mode=DownloadMode.BROWSER, headless=False,
                                                 update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    else:
                                        print("输入错误，请重新输入")
                            elif choice == "7":
                                try:
                                    from tkinter import filedialog
                                    folder_path = filedialog.askdirectory(title='选择文件夹')
                                except ImportError:
                                    filedialog = None
                                    folder_path = input("请输入文件夹路径")
                                if folder_path:
                                    self.set(mode=DownloadMode.BROWSER, user_data_dir=folder_path,
                                             update_config=True, create_if_missing=False)
                                    self.save_config()
                                    print(f"选择的路径：{folder_path}")
                                else:
                                    print("未选择路径")
                                    continue

                    elif option == "3":
                        website = Website.FANQIE
                        site_api = self.config.api[website]
                        provider = site_api.get_provider()
                        if not provider:
                            first_key = next(iter(site_api.providers))
                            site_api.option = first_key
                            provider = site_api.providers[first_key]
                        while True:
                            print(f'''
API提供商配置 (当前提供商: {provider.name})
1. 启用状态 (当前: {provider.enabled})
2. 最大重试次数 (当前: {provider.max_retry})
3. 超时时间 (当前: {provider.timeout}s)
4. 重试间隔 (当前: {provider.interval}s)
5. 延迟范围 (当前: {provider.delay[0]}-{provider.delay[1]}s)
6. API密钥 (当前: {provider.key})
7. 端点 (当前: {provider.endpoint})
8. 请求头 (当前: {provider.headers})
输入q退出:''')
                            choice = input().strip()
                            if choice == "q":
                                break
                            elif choice == "1":
                                while True:
                                    val = input("是否启用(y/n): ").strip()
                                    if val == "q": break
                                    if val == "y":
                                        provider.enabled = True
                                        self.save_config()
                                        break
                                    elif val == "n":
                                        provider.enabled = False
                                        self.save_config()
                                        break
                                    else:
                                        print("输入错误，请重新输入")
                                        continue
                            elif choice == "2":
                                while True:
                                    val = input("请输入最大重试次数: ").strip()
                                    if val == "q": break
                                    try:
                                        self.set(mode=DownloadMode.API,api_name=provider.name, max_retry=int(val),update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "3":
                                while True:
                                    val = input("请输入超时时间(秒): ").strip()
                                    if val == "q": break
                                    try:
                                        self.set(mode=DownloadMode.API,api_name=provider.name, timeout=int(val),update_config=True, create_if_missing=False)
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "4":
                                while True:
                                    val = input("请输入重试间隔(秒): ").strip()
                                    if val == "q": break
                                    try:
                                        provider.interval = float(val)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "5":
                                while True:
                                    val = input("请输入延迟范围(下限 上限，空格分隔): ").strip()
                                    if val == "q": break
                                    parts = val.split()
                                    if len(parts) == 2:
                                        try:
                                            low = float(parts[0])
                                            high = float(parts[1])
                                            delay = [low, high]
                                            self.set(mode=DownloadMode.API,api_name=provider.name,delay=delay,update_config=True, create_if_missing=False)
                                            self.save_config()
                                            break
                                        except ValueError:
                                            print("输入错误，请重新输入")
                                    else:
                                        print("必须输入两个数字")
                            elif choice == "6":
                                val = input("请输入API密钥: ").strip()
                                if val != "q":
                                    self.set(mode=DownloadMode.API,api_name=provider.name,update_config=True,api_key=val, create_if_missing=False)
                                    self.save_config()
                            elif choice == "7":
                                print("请输入请求头(JSON格式，如 {\"User-Agent\": \"...\"}):")
                                val = input().strip()
                                if val != "q":
                                    try:
                                        headers = json.loads(val)
                                        if isinstance(headers, dict):
                                            provider.headers = headers
                                            self.save_config()
                                        else:
                                            print("输入必须是字典")
                                    except json.JSONDecodeError:
                                        print("JSON解析错误")
                            elif choice == "8":
                                print("请输入请求参数(JSON格式):")
                                val = input().strip()
                                if val != "q":
                                    try:
                                        params = json.loads(val)
                                        if isinstance(params, dict):
                                            provider.params = params
                                            self.save_config()
                                        else:
                                            print("输入必须是字典")
                                    except json.JSONDecodeError:
                                        print("JSON解析错误")
                            else:
                                print("无效选项，请重新输入")

                    elif option == "4":
                        website = None
                        while True:
                            website_choice = input(
        """
请选择网站：
1.番茄
2.起点
3.笔趣阁(www.biqugequ.org)
输入q退出：""").strip()
                            if website_choice == "q":
                                break
                            elif website_choice == "1":
                                website = Website.FANQIE
                            elif website_choice == "2":
                                website = Website.QIDIAN
                            elif website_choice == "3":
                                website = Website.BIQUGE
                            else:
                                print("输入错误")
                                continue
                        if website is None:
                            continue
                        req_config = self.config.requests[website]
                        while True:
                            print(f'''
Requests配置 (网站: {website})
1. 最大重试次数 (当前: {req_config.max_retry})
2. 超时时间 (当前: {req_config.timeout}s)
3. 重试间隔 (当前: {req_config.interval}s)
4. 延迟范围 (当前: {req_config.delay[0]}-{req_config.delay[1]}s)
5. Cookies (当前: {req_config.cookies})
6. 请求头 (当前: {req_config.headers})
7. 代理 (当前: {req_config.proxies})
输入q退出:''')
                            choice = input().strip()
                            if choice == "q":
                                break
                            elif choice == "1":
                                while True:
                                    val = input("请输入最大重试次数: ").strip()
                                    if val == "q": break
                                    try:
                                        self.set(mode=DownloadMode.REQUESTS,website=website,max_retry=int(val), create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "2":
                                while True:
                                    val = input("请输入超时时间(秒): ").strip()
                                    if val == "q": break
                                    try:
                                        self.set(mode=DownloadMode.REQUESTS,website=website,timeout=int(val), create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "3":
                                while True:
                                    val = input("请输入重试间隔(秒): ").strip()
                                    if val == "q": break
                                    try:
                                        self.set(mode=DownloadMode.REQUESTS,website=website,interval=float(val), create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "4":
                                while True:
                                    val = input("请输入延迟范围(下限 上限，空格分隔): ").strip()
                                    if val == "q": break
                                    parts = val.split()
                                    if len(parts) == 2:
                                        try:
                                            low = float(parts[0])
                                            high = float(parts[1])
                                            self.set(mode=DownloadMode.REQUESTS, website=website,delay=[low,high], create_if_missing=False)
                                            self.save_config()
                                            break
                                        except ValueError:
                                            print("输入错误，请重新输入")
                                    else:
                                        print("必须输入两个数字")
                            elif choice == "5":
                                val = input("请输入Cookies字符串: ").strip()
                                if val != "q":
                                    req_config.cookies = val
                                    self.save_config()
                            elif choice == "6":
                                print("请输入请求头(JSON格式):")
                                val = input().strip()
                                if val != "q":
                                    try:
                                        headers = json.loads(val)
                                        if isinstance(headers, dict):
                                            req_config.headers = headers
                                            self.save_config()
                                        else:
                                            print("输入必须是字典")
                                    except json.JSONDecodeError:
                                        print("JSON解析错误")
                            elif choice == "7":
                                print("请输入代理(JSON格式，如 {\"http\": \"http://proxy:8080\"}):")
                                val = input().strip()
                                if val != "q":
                                    try:
                                        proxies = json.loads(val)
                                        if isinstance(proxies, dict):
                                            self.set(mode=DownloadMode.REQUESTS, website=website,proxies=proxies, create_if_missing=False)
                                            self.save_config()
                                        else:
                                            print("输入必须是字典")
                                    except json.JSONDecodeError:
                                        print("JSON解析错误")
                            else:
                                print("无效选项，请重新输入")

                    # 5. 保存方式设置
                    elif option == "5":
                        continue
                        print("暂未开发完善")
                        save_config = self.config.save_method
                        while True:
                            print('''
保存方式设置:
2. JSON配置
3. TXT配置
4. HTML配置
5. EPUB配置
6. 图片配置 (img)
输入q退出:''')
                            choice = input().strip()
                            if choice == "q":
                                break

                            # JSON配置
                            elif choice == "1":
                                while True:
                                    print(f'''
JSON配置
1. 启用 (当前: {save_config.json.enable})
2. 文件名 (当前: {save_config.json.file_name})
3. 输出目录 (当前: {save_config.json.output_dir})
4. 缩进空格数 (当前: {save_config.json.indent})
5. 保存间隔 (当前: {save_config.json.save_interval})
6. 确保ASCII (当前: {save_config.json.ensure_ascii})
输入q退出:''')
                                    sub_choice = input().strip()
                                    if sub_choice == "q":
                                        break
                                    elif sub_choice == "1":
                                        while True:
                                            val = input("是否启用(y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.json.enable = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.json.enable = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "2":
                                        val = input("请输入文件名(留空自动): ").strip()
                                        if val != "q":
                                            save_config.json.file_name = val if val else None
                                            self.save_config()
                                    elif sub_choice == "3":
                                        folder = filedialog.askdirectory(title="选择JSON输出目录")
                                        if folder:
                                            save_config.json.output_dir = folder
                                            self.save_config()
                                            print(f"已设置为: {folder}")
                                        else:
                                            print("未选择目录")
                                    elif sub_choice == "4":
                                        while True:
                                            val = input("请输入缩进空格数: ").strip()
                                            if val == "q": break
                                            try:
                                                save_config.json.indent = int(val)
                                                self.save_config()
                                                break
                                            except ValueError:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "5":
                                        while True:
                                            val = input("请输入保存间隔(章节数): ").strip()
                                            if val == "q": break
                                            try:
                                                save_config.json.save_interval = int(val)
                                                self.save_config()
                                                break
                                            except ValueError:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "6":
                                        while True:
                                            val = input("是否确保ASCII (y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.json.ensure_ascii = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.json.ensure_ascii = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    else:
                                        print("无效选项")

                            # TXT配置
                            elif choice == "2":
                                while True:
                                    print(f'''
TXT配置
1. 启用 (当前: {save_config.txt.enable})
2. 文件名 (当前: {save_config.txt.file_name})
3. 输出目录 (当前: {save_config.txt.output_dir})
4. 章节间隔 (当前: {save_config.txt.chapters_per_file})
5. 最大文件大小 (当前: {save_config.txt.file_size} MB)
6. 编码 (当前: {save_config.txt.encoding})
输入q退出:''')
                                    sub_choice = input().strip()
                                    if sub_choice == "q":
                                        break
                                    elif sub_choice == "1":
                                        while True:
                                            val = input("是否启用(y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.txt.enable = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.txt.enable = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "2":
                                        val = input("请输入文件名(留空自动): ").strip()
                                        if val != "q":
                                            save_config.txt.file_name = val if val else None
                                            self.save_config()
                                    elif sub_choice == "3":
                                        folder = filedialog.askdirectory(title="选择TXT输出目录")
                                        if folder:
                                            save_config.txt.output_dir = folder
                                            self.save_config()
                                            print(f"已设置为: {folder}")
                                        else:
                                            print("未选择目录")
                                    elif sub_choice == "4":
                                        while True:
                                            val = input("请输入章节间隔(空行数量): ").strip()
                                            if val == "q": break
                                            try:
                                                save_config.txt.chapters_per_file = int(val)
                                                self.save_config()
                                                break
                                            except ValueError:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "5":
                                        while True:
                                            val = input("请输入最大文件大小(MB，-1表示无限制): ").strip()
                                            if val == "q": break
                                            try:
                                                save_config.txt.file_size = int(val)
                                                self.save_config()
                                                break
                                            except ValueError:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "6":
                                        val = input("请输入编码(如 utf-8): ").strip()
                                        if val != "q":
                                            save_config.txt.encoding = val
                                            self.save_config()
                                    else:
                                        print("无效选项")

                            # HTML配置
                            elif choice == "3":
                                while True:
                                    print(f'''
HTML配置
1. 启用 (当前: {save_config.html.enable})
2. 文件名 (当前: {save_config.html.file_name})
3. 输出目录 (当前: {save_config.html.output_dir})
4. 单文件 (当前: {save_config.html.one_file})
5. 模板 (当前: {save_config.html.template})
输入q退出:''')
                                    sub_choice = input().strip()
                                    if sub_choice == "q":
                                        break
                                    elif sub_choice == "1":
                                        while True:
                                            val = input("是否启用(y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.html.enable = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.html.enable = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "2":
                                        val = input("请输入文件名(留空自动): ").strip()
                                        if val != "q":
                                            save_config.html.file_name = val if val else None
                                            self.save_config()
                                    elif sub_choice == "3":
                                        folder = filedialog.askdirectory(title="选择HTML输出目录")
                                        if folder:
                                            save_config.html.output_dir = folder
                                            self.save_config()
                                            print(f"已设置为: {folder}")
                                        else:
                                            print("未选择目录")
                                    elif sub_choice == "4":
                                        while True:
                                            val = input("是否单文件(y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.html.one_file = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.html.one_file = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "5":
                                        val = input("请输入模板名称: ").strip()
                                        if val != "q":
                                            save_config.html.template = val
                                            self.save_config()
                                    else:
                                        print("无效选项")

                            # EPUB配置
                            elif choice == "4":
                                while True:
                                    print(f'''
EPUB配置
1. 启用 (当前: {save_config.epub.enable})
2. 文件名 (当前: {save_config.epub.file_name})
3. 输出目录 (当前: {save_config.epub.output_dir})
4. CSS样式 (当前: {save_config.epub.css_style})
5. 包含目录 (当前: {save_config.epub.include_toc})
输入q退出:''')
                                    sub_choice = input().strip()
                                    if sub_choice == "q":
                                        break
                                    elif sub_choice == "1":
                                        while True:
                                            val = input("是否启用(y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.epub.enable = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.epub.enable = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "2":
                                        val = input("请输入文件名(留空自动): ").strip()
                                        if val != "q":
                                            save_config.epub.file_name = val if val else None
                                            self.save_config()
                                    elif sub_choice == "3":
                                        folder = filedialog.askdirectory(title="选择EPUB输出目录")
                                        if folder:
                                            save_config.epub.output_dir = folder
                                            self.save_config()
                                            print(f"已设置为: {folder}")
                                        else:
                                            print("未选择目录")
                                    elif sub_choice == "4":
                                        val = input("请输入CSS样式名称: ").strip()
                                        if val != "q":
                                            save_config.epub.css_style = val
                                            self.save_config()
                                    elif sub_choice == "5":
                                        while True:
                                            val = input("是否包含目录(y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.epub.include_toc = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.epub.include_toc = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    else:
                                        print("无效选项")

                            # 图片配置
                            elif choice == "5":
                                while True:
                                    print(f'''
图片配置
1. 启用 (当前: {save_config.img.enable})
2. 文件名 (当前: {save_config.img.file_name})
3. 输出目录 (当前: {save_config.img.output_dir})
4. 方法 (当前: {save_config.img.method})
5. 扩展名 (当前: {save_config.img.extension})
输入q退出:''')
                                    sub_choice = input().strip()
                                    if sub_choice == "q":
                                        break
                                    elif sub_choice == "1":
                                        while True:
                                            val = input("是否启用(y/n): ").strip()
                                            if val == "q": break
                                            if val == "y":
                                                save_config.img.enable = True
                                                self.save_config()
                                                break
                                            elif val == "n":
                                                save_config.img.enable = False
                                                self.save_config()
                                                break
                                            else:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "2":
                                        val = input("请输入文件名(留空自动): ").strip()
                                        if val != "q":
                                            save_config.img.file_name = val if val else None
                                            self.save_config()
                                    elif sub_choice == "3":
                                        folder = filedialog.askdirectory(title="选择图片输出目录")
                                        if folder:
                                            save_config.img.output_dir = folder
                                            self.save_config()
                                            print(f"已设置为: {folder}")
                                        else:
                                            print("未选择目录")
                                    elif sub_choice == "4":
                                        while True:
                                            val = input("请输入方法(0-?): ").strip()
                                            if val == "q": break
                                            try:
                                                save_config.img.method = int(val)
                                                self.save_config()
                                                break
                                            except ValueError:
                                                print("输入错误，请重新输入")
                                    elif sub_choice == "5":
                                        val = input("请输入扩展名(如 .png): ").strip()
                                        if val != "q":
                                            save_config.img.extension = val
                                            self.save_config()
                                    else:
                                        print("无效选项")
                            else:
                                print("无效选项")

                    # 6. 备份设置
                    elif option == "6":
                        backup = self.config.auto_backup
                        while True:
                            print(f'''
备份设置
1. 自动备份 (当前: {backup.auto})
2. 备份间隔(秒) (当前: {backup.interval})
3. 备份目录 (当前: {backup.backup_dir})
4. 备份文件名 (当前: {backup.name})
输入q退出:''')
                            choice = input().strip()
                            if choice == "q":
                                break
                            elif choice == "1":
                                while True:
                                    val = input("是否自动备份(y/n): ").strip()
                                    if val == "q": break
                                    if val == "y":
                                        self.set(backup_auto=True,update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    elif val == "n":
                                        self.set(backup_auto=False,update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    else:
                                        print("输入错误，请重新输入")
                            elif choice == "2":
                                while True:
                                    val = input("请输入备份间隔(秒): ").strip()
                                    if val == "q": break
                                    try:
                                        self.set(backup_interval=int(val),update_config=True, create_if_missing=False)
                                        self.save_config()
                                        break
                                    except ValueError:
                                        print("输入错误，请重新输入")
                            elif choice == "3":
                                try:
                                    from tkinter import filedialog
                                    folder = filedialog.askdirectory(title="选择备份目录")
                                except ImportError:
                                    filedialog = None
                                    folder = input("请输入备份路径")
                                if folder:
                                    self.set(backup_dir=folder,update_config=True, create_if_missing=False)
                                    self.save_config()
                                    print(f"已设置为: {folder}")
                                else:
                                    print("未选择目录")
                            elif choice == "4":
                                val = input("请输入备份文件名: ").strip()
                                if val != "q":
                                    self.set(backup_name=val,update_config=True, create_if_missing=False)
                                    self.save_config()
                            else:
                                print("无效选项")

                    else:
                        print("无效选项，请重新输入")

    def update_novel(self, group):
        url,website = parse_url(group.url)
        if not os.path.exists(group.file_path):
            print(f"{group.file_path} 不存在")
            self.set(config = group, website = website)
            novel = self.get_info(url=url)
            self.config.groups.update(self.novel.group)
            if novel.total:
                orders = list(range(1,len(novel.chapters)+1))
            else:
                orders = list(range(1,25001))
            self.__download(download_url=url, orders=orders)
            return
        print("正在更新")
        history = self.read_novel(group.file_path)
        if not history:
            print("历史版本为空")
            return

        local_chapters = {}  # order -> Chapter
        for novel in reversed(history):
            for ch in novel.chapters:
                if ch.order not in local_chapters:
                    local_chapters[ch.order] = ch

        self.set(config=group, website=website)

        remote_novel = self.get_info(url=group.url)
        target_novel = remote_novel

        need_download_orders = []

        if remote_novel.total:
            for remote_ch in remote_novel.chapters:
                order = remote_ch.order
                local_ch = local_chapters.get(order)
                if local_ch and local_ch.is_complete:
                    remote_ch.content = local_ch.content
                    remote_ch.images = local_ch.images
                    remote_ch.is_complete = True
                    remote_ch.timestamp = local_ch.timestamp
                    target_novel.update(remote_ch)
                else:
                    target_novel.update(remote_ch)
                    need_download_orders.append(order)
            need_save_orders = [i for i in range(1,remote_novel.total+1) if i not in need_download_orders]
            need_save_chapters = [remote_novel.find_chapter(order) for order in need_save_orders]
            pass
        else:
            all_possible_orders = list(range(1,25001))
            need_download_orders = [
                o for o in all_possible_orders
                if o not in local_chapters or not local_chapters[o].is_complete
            ]
            need_save_orders = [i for i in all_possible_orders if i not in need_download_orders]
            need_save_chapters = [remote_novel.find_chapter(order) for order in need_save_orders]
        self.save_novel(need_save_chapters)
        need_download_orders = sorted(set(need_download_orders))
        del history
        self.__download(download_url=group.url, orders=need_download_orders,)

    def download_novel(self,download_url):
        url,website = parse_url(download_url)
        if website == Website.OTHER:
            print("链接不正确，请重新输入")
        if nd.config.groups.find_group(group_name=self.config.group,url=url):
            found_group = nd.config.groups.find_group(url=url)[-1]
            self.set(config=found_group,website=website)
            return self.update_novel(found_group)
        else:
            self.set(config = self.config, website = website)
            novel = self.get_info(url=url)
            self.config.groups.update(self.novel.group)
            if novel.total:
                orders = list(range(1,len(novel.chapters)+1))
            else:
                orders = list(range(1,25001))
            self.__download(download_url=url, orders=orders)
        self.auto_backup()
        return None
if __name__ == "__main__":
    config_method = check()
    """
    if len(sys.argv) > 1:
        nd = ND()
        nd.cli_download_novel()"""
    while True:
        nd=ND(config_method)
        print(f"当前：User:{nd.config.user}   Group:{nd.config.group}  mode:{nd.config.mode}")
        try:
            select = input(
                "\n"
                "请输入选项 | 链接:\n"
                "0.网站登录：\n"
                "1.搜索 & 下载：\n"
                "2.更新：\n"
                "3.下载：\n"
                "4.批量下载：\n"
                "5.设置：\n"
                "6.备份：\n"
            ).strip()

            if select:
                if select == "0":
                    print("\n需要进行浏览器操作\n")
                    website_option = input("""请选择网站：
1.番茄：
2.起点：
3.笔趣阁(www.biqugequ.org)
：""").strip()

                    print("登录后按下任意键继续..")
                    time.sleep(0.5)
                    if website_option == '1':
                        login_url = "https://fanqienovel.com/main/writer/login"
                        website_str = "fanqie"
                    elif website_option == "2":
                        login_url = "https://www.qidian.com"
                        website_str = "qidian"
                    elif website_option == '3':
                        login_url = "https://biqugequ.org"
                        website_str = "biquge"
                    else:
                        print("请指定网站")
                        continue
                    from DrissionPage import Chromium,ChromiumOptions
                    co = ChromiumOptions().set_user_data_path(nd.config.browser.user_data_dir)
                    driver = Chromium(addr_or_opts=co)
                    tab = driver.new_tab()
                    tab.get(login_url)
                    input()
                    cookie = tab.cookies()
                    cookies = "; ".join([f"{c['name']}={c['value']}" for c in cookie])
                    print(f"cookie: {cookies}\n请妥善保管")
                    choice = input("是否保存cookies(y/n)").strip()
                    if choice == "y":
                        nd.config.requests[website_str].cookies = cookies
                        nd.save_config()
                elif select == "1":nd.search()
                elif select == "2":
                    groups = nd.config.groups
                    print("\n请选择数字:")
                    result:list[Group] = []
                    for group_name,group_tuple in groups.groups.items():
                            result.extend(list(group_tuple))
                    for index in range(len(result)):
                        print(f"{index+1}.{result[index].novel_name}  群组：{result[index].group_name} URL：{result[index].url}")
                    ranges = input()
                    update_range = range_split(ranges, len(result))  # 分割为纯数字型列表
                    for index in update_range:
                        nd.update_novel(group=result[index-1])
                    del groups
                elif select == "3":
                    input_url = input("请输入小说链接：")
                    nd.download_novel(download_url=input_url)
                elif select == "4":
                    filename = os.path.join("data", "Local", "urls.txt")
                    if not os.path.exists(filename):
                        open(filename, encoding="utf-8").close()
                    print(
                        """将打开urls.txt,请在文件中输入小说链接，一行一个。输入完成后请保存并关闭文件，然后按 Enter 键继续...""")
                    time.sleep(0.5)
                    system = platform.system()
                    if system == "Windows":
                        os.startfile(filename)
                    elif system == "Darwin":  # macOS
                        subprocess.run(['open', filename])
                    else:  # Linux 和其他Unix系统
                        try:
                            subprocess.run(['xdg-open', filename])
                        except FileNotFoundError:
                            print("无法打开文件，请检查系统")
                    input()
                    nd_list = []
                    with open(filename, encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("#"): continue
                            nd_example = ND()
                            nd_list.append(nd_example)
                            nd_example.download_novel(line.strip())
                elif select == "5":
                    nd.setting()
                elif select.startswith("https://"):
                    nd.download_novel(download_url=select)
        except KeyboardInterrupt:
            exit(0)