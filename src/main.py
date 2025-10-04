# -*- coding: utf-8 -*-
import faulthandler
import json
import logging
import os
import re
import sys
import time
import tkinter as tk
import traceback
import zipfile
from datetime import datetime
from pathlib import Path
from tkinter import filedialog

from colorama import init, Fore
from tqdm import tqdm

import Check
from Biquge import Biquge
from Fanqie import Fanqie
from Qidian import Qidian
from RunDriver import RunDriver
from Save import Save
from SetConfig import SetConfig

faulthandler.enable()
init(autoreset=True)
"""当前版本暂未完全测试，但是下载和更新功能(Chrome模式)可以使用"""


def global_exception_handler(exctype, value, tb):
    """全局异常处理器"""
    error_msg = ''.join(traceback.format_exception(exctype, value, tb))
    logger.error(f"程序崩溃:\n{error_msg}")
    # 将错误信息写入单独文件
    with open(os.path.join(os.getenv("Temp"), "logs", f"{datetime.now().strftime('%Y-%m-%d')}.log"), "a") as error_f:
        error_f.write(f"崩溃时间: {datetime.now()}\n")
        error_f.write(f"异常类型: {exctype}\n")
        error_f.write(f"异常值: {value}\n")
        error_f.write("追踪信息:\n")
        error_f.write(error_msg + '\n\n')

    # 显示错误信息给用户
    print(f"程序发生错误，详情已保存至日志文件。")
    code = input("是否弹出所在文件夹？（y/n）").lower()
    if 'y' in code or 'Y' in code:
        os.startfile(os.path.join(os.getenv("Temp"), "logs"))  # 弹出指定文件夹
    sys.exit(1)


def backup(user_manage: dict,
           backup_config: dict,
           auto: bool = False) -> dict | bool:
    """
    备份UserConfig.json和用户下的所有小说的JSON
    """
    user = user_manage['USER']
    backup_path_list = user_manage['USERS'][user]
    # 获取备份目录
    if auto:  # 隐式自动保存
        set_dir = backup_config['Dir']
    else:  # 显式保存
        if backup_config.get("Pop_up_folder", False):  # 是否弹出文件夹选择框
            root = tk.Tk()
            root.withdraw()  # 隐藏主窗口
            print("请在文件夹选择框选择文件夹：")
            time.sleep(1)
            set_dir = filedialog.askdirectory()  # 弹出选择文件夹对话框
            root.destroy()
        else:
            set_dir = backup_config['Dir']

    if not set_dir:  # 备份保存目录为空时
        if not auto:
            print("未指定目录，已退出")
        return False
    else:
        # 防止目录不合理报错
        try:
            os.makedirs(set_dir, exist_ok=True)
        except OSError as e:
            print(e)
            return False  # 跳过
    # 获取备份名称并格式化
    backup_name = backup_config.get("Name")
    transform_list = re.findall(r'<.+?>', backup_name)
    for index in transform_list:
        # 替换为当前用户
        if '<User>' == index:
            backup_name = backup_name.replace(index, user, 1)
        # 替换为当前时间
        if index.startswith('<T:'):
            time_format = re.search(r"<T:'(.+)'>", index).group(1)
            time_str = time.strftime(time_format, time.localtime())
            backup_name = backup_name.replace(index, time_str, 1)
    # 备份保存路径
    set_path = Path(set_dir) / backup_name
    try:
        with zipfile.ZipFile(set_path, 'w', zipfile.ZIP_STORED) as zipf:
            for path in backup_path_list.keys():
                # UserConfig,json加入zip
                if 'User_config_path' == path:
                    zipf.write(backup_path_list['User_config_path'], "UserConfig.json")
                # 所有小说JSON加入zip
                if "Base_dir" == path:
                    for root, _, files in os.walk(backup_path_list[path]):
                        for file in files:
                            if file.endswith(".json"):
                                json_path = Path(root) / file
                                zipf.write(json_path, os.path.join('json', file))

        backup_config['Last_time'] = time.time()
        return backup_config
    except Exception as e:
        print(f"无法备份,原因：{e}")
        return False


def range_split(deal_range: str,
                total_list: int | None) -> list[int]:
    """
    处理范围字符串，将其转换为索引列表。
    """
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
    sorted_range = sorted(result_range)

    return sorted_range


class NovelDownloader:

    def update(self):
        file_name = self.Class_Config.mems[self.Class_Config.Group][self.download_url] + '.json'  # 需要读取的文件全名
        json_path = Path(self.Class_Config.Base_dir) / file_name  # 路径
        if not os.path.exists(json_path):
            print('json文件被移动或不存在')
        else:
            with open(json_path, "r", encoding='utf-8') as f:
                read_data = json.load(f)
                self.Class_Novel.novel['chapters'] = read_data['chapters']  # 获取章节的同时更新小说信息
                self.Class_Novel.novel['info']['name'] = read_data['info']['name']  # 防止小说名称改变而找不到根json
            # 需要更新的和不完整的链接及标题
            self.Class_Novel.down_title_list = [title for title in self.Class_Novel.down_title_list if
                                                title not in self.Class_Novel.novel['chapters'].keys() or not
                                                self.Class_Novel.novel['chapters'][title]['integrity']]
            all_title_url = dict(
                zip(self.Class_Novel.all_title_list, self.Class_Novel.all_url_list))
            self.Class_Novel.down_url_list = [all_title_url[title] for title in
                                              self.Class_Novel.down_title_list]
            return True
        return False

    def load_down_args(self, url):

        url = url.split('?')[0].strip()  # 不带参数的url
        if 'https://changdunovel.com/wap/' in url:  # 处理番茄小说的分享链接
            book_id = re.search(r"book_id=(\d+)", url).group(1)
            url = 'https://fanqienovel.com/page/' + book_id
        if "https://magev6.if.qidian.com/h5/share" in url:
            book_id = re.search(r"bookld=(\d+)", url).group(1)
            url = 'https://www.qidian.com/book/' + book_id
        if 'fanqienovel.com' in url:
            self.Class_Novel = self.Class_Fanqie
        elif 'qidian.com' in url:
            self.Class_Novel = self.Class_Qidian
        elif 'biqugequ.org' in url:
            self.Class_Novel = self.Class_Biquge
        else:
            print('不支持该网站，请检查链接')
            raise ValueError(f"NovelDownloader:The website corresponding to this url does not support\nUrl: {url}")

        self.download_url = url  # 全局的url
        self.Class_Config.set_config(url)  # 通过url设置配置
        if self.Class_Config.Get_mode == 0:  # 选择以Chrome获取
            self.Class_Driver.config(user_data_dir=self.Class_Config.User_data_dir, port=self.Class_Config.Port,
                                     # 配置Chrome参数
                                     headless=self.Class_Config.Headless)
            self.Class_Driver.run()  # Chrome启动！
        if not self.Class_Novel.get_page(self.download_url):  # 获取小说目录页的一些信息
            return False
        if self.Class_Config.Novel_update:
            self.update()  # 获取需更新小说标题及链接
            self.Class_Save.config(self.Class_Novel, self.Class_Config)  # 初始化保存配置
            self.Class_Save.save(full_save=True)  # 覆写模式保存
        if self.range:
            self.range = range_split(self.range, len(self.Class_Novel.down_title_list))  # 分割范围成连续数字列表
            self.Class_Novel.down_title_list = [self.Class_Novel.down_title_list[index - 1] for index in self.range]
            self.Class_Novel.down_url_list = [self.Class_Novel.down_url_list[index - 1] for index in self.range]
        self.Class_Save.config(self.Class_Novel, self.Class_Config)  # 初始化保存配置
        return True

    def _download(self):
        index = self.Class_Novel.all_title_list.index(self.Class_Novel.down_title_list[0]) - 1
        for title, url in zip(self.Class_Novel.down_title_list, self.Class_Novel.down_url_list):
            index += 1
            if not self.Class_Novel.download(title, url, index, self.download_url): return False
            if self.Class_Config.Save_method: pass
            self.Class_Save.save(title=title)  # 保存
            self.down_progress.update(1)
        return True

    def download_novel(self):
        with tqdm(total=len(self.Class_Novel.down_title_list),
                  desc=self.Class_Novel.novel['info']['name']) as self.down_progress:
            try:
                self._download()
                # 多线程启动self._download() 暂未实现
                for thread_id in range(self.Class_Config.Threads_num):
                    pass
            except KeyboardInterrupt:
                print("已退出..")

    def func(self):
        backup_config = self.Class_Config.User_config.get('Backup', {})
        if backup_config.get("Auto", False):
            last_backup_time = backup_config.get("Last_time", 0)
            now_time = time.time()
            if now_time - last_backup_time > 86400:
                backup_dir = backup_config.get("dir")
                backup_dict = self.Class_Config.User_manage['USERS'][self.Class_Config.USER]
                backup_path = backup(backup_dict, backup_dir)
                print(f"已自动保存成功,已保存在 {backup_path}")

        while True:
            # 自动备份
            try:  # 懒得测新功能所以就用try-except了
                backup_config = self.Class_Config.User_config.get('Backup', {})
                if backup_config.get('Auto', False):
                    auto_save_method = backup_config.get('Auto_save_method', '')
                    if auto_save_method.startswith('T:'):
                        time_interval = re.search(r"(\d+)", auto_save_method).group(1)
                        if time_interval:
                            now_time = time.time()
                            last_backup_time = backup_config.get('Last_time', -1)
                            if now_time - last_backup_time > time_interval:
                                new_backup_config = backup(self.Class_Config.User_manage, backup_config, auto=True)
                                self.Class_Config.User_config["Backup"] = new_backup_config
                                self.Class_Config.save_config(1)
                        else:
                            print(f"{Fore.YELLOW}注意：保存方式（以时间保存）指定的时间间隔格式不正确，请检查其设置")
                # 重新加载默认Config
                self.Class_Config.load()
                Check.main()
            except Exception as e:
                print(e)
                pass
            try:
                saved_mems = self.Class_Config.mems
                urls_para = []
                urls = []  # 所有成员
                for group in saved_mems.keys():
                    if group == "Version": continue
                    for url in saved_mems[group].keys():
                        name = saved_mems[group][url]
                        urls.append(url)
                        urls_para.append((group, name, url))

                print(f"\n当前账户：{self.Class_Config.USER}    当前分组：{self.Class_Config.GROUP}")
                self.select = input(
                    """
请输入功能:
0.网站登录：
1.更新小说：
2.下载：
3.批量下载：
4.指定章节下载:
5.设置:
6.备份：
""").strip()
                match self.select:  # 嵌套严重，被绕晕了..
                    case '0':
                        option = input("""请选择网站：
1.番茄：
2.起点：
3.(新)笔趣阁：
""")
                        # 直接退出
                        if not option and re.match(r"^\d$", option):
                            print('输入错误')
                            continue
                        # 配置Chrome
                        self.Class_Driver.config(user_data_dir=self.Class_Config.User_data_dir,
                                                 port=self.Class_Config.Port, headless=False)
                        tab = self.Class_Driver.run()  # Chrome启动
                        match option:
                            case '1':
                                tab.get("https://fanqienovel.com/main/writer/login")
                                input("登录后按下任意键继续..")
                                html = tab.raw_data  # html数据
                                self.Class_Fanqie.user_state_for_html(html)
                                match self.Class_Fanqie.user_state_code:
                                    case -1:  # 未登录
                                        self.Class_Config.User_config['Browser']['State']['Fanqie'] = -1
                                    case 0:  # 已登录但无vip
                                        self.Class_Config.User_config['Browser']['State']['Fanqie'] = 0
                                    case 1:  # 有vip
                                        self.Class_Config.User_config['Browser']['State']['Fanqie'] = 1
                                self.Class_Config.save_config(1)  # 保存状态

                            case '2':
                                tab.get("https://www.qidian.com/")
                                input("登录后按下任意键继续..")

                            case '3':
                                tab.get("https://www.biqugequ.org/")
                                input("登录后按下任意键继续..")

                    case "1":
                        # 按Group，name输出
                        for sequence in range(len(urls_para)):  print(
                            f'{sequence + 1}.群组：{urls_para[sequence][0]} 小说名：{urls_para[sequence][1]}')
                        choice = input('请输入数字或范围（如1-3,5,7-9；last:3；all）')
                        if not choice:
                            print('输入错误')
                            continue
                        update_range = range_split(choice, len(urls_para))  # 分割为纯数字型列表
                        for index in update_range:
                            self.download_url = urls_para[index - 1][2]
                            self.Class_Config.Novel_update = True  # 标记为更新
                            self.load_down_args(self.download_url)  # 配置
                            self.download_novel()  # 下载

                    case "2":
                        input_url = input('请输入小说链接:')
                        if not input_url:
                            print('输入错误')
                            continue
                        if input_url in urls:
                            print("当前链接存在，自动更新中…")
                            self.Class_Config.Novel_update = True  # 标记为更新
                        self.load_down_args(input_url)  # 配置
                        self.download_novel()  # 下载

                    case "3":
                        print(
                            """将打开urls.txt,请在文件中输入小说链接，一行一个。\
                            输入完成后请保存并关闭文件，然后按 Enter 键继续...""")
                        time.sleep(0.5)
                        os.startfile('data\\Local\\urls.txt')  # 弹出url.txt（Windows）
                        input()
                        with open('data\\Local\\urls.txt', 'r', encoding='utf-8') as f_:
                            for line in f_:
                                if not line:
                                    continue
                                if line in urls:
                                    print("当前链接存在，自动更新中…")
                                    self.Class_Novel.Novel_update = True  # 标记为更新
                                self.load_down_args(line)
                                self.download_novel()

                    case "4":
                        para = input('请输入小说链接:')
                        if not para:
                            continue
                        novel_range = input('请输入章节范围(如1-3,5,7-9):')
                        self.range = novel_range
                        self.download_url = self.load_down_args(self.download_url)
                        self.download_novel()
                        """
建议直接通过JSON文件修改配置，这样更快更灵活.（若精通）
"""
                    case "5":
                        print("pass")
                    case "6":
                        # 获取Base的路径 和 User_config.json的路径
                        user_manage = self.Class_Config.User_manage
                        # 备份配置
                        backup_config = self.Class_Config.User_config.get("Backup")
                        # 默认备份配置
                        default_backup_item = {
                            "Auto": False,
                            "Auto_save_method": "T:86400",
                            "Dir": "C:\\\\",
                            "Name": "Novel_backup <User><T:'%Y-%m-%d'>.zip",
                            "Last_time": -1,
                            "Pop_up_folder": True
                        }

                        if backup_config is None:
                            cho = input('''检测到UserConfig没有保存配置，是否添加？ (y/n)\n
配置添加：
1.自动保存(false) 
2.自动保存方式(每隔86400秒自动保存) 
3.保存路径(C:\\\\) 
4.备份名字：Novel_backup <User><T:'%Y-%m-%d'>.zip 
5.上一次保存时间(-1) 
5.显式备份自动弹出文件夹选择对话框(true)
                                        ''')

                            if cho.lower() == 'y':
                                self.Class_Config.User_config["Backup"] = default_backup_item
                                backup_config = default_backup_item
                                self.Class_Config.save_config(1)
                            else:
                                backup_config = default_backup_item  # 使用默认备份方式

                        new_backup_config = backup(backup_config, user_manage, auto=False)
                        self.Class_Config.User_config["Backup"] = new_backup_config
                        self.Class_Config.save_config(1)

            except ValueError as e:
                if str(e).startswith("NovelDownloader:"):
                    continue
                else:
                    raise
            except KeyboardInterrupt:
                code = input("是否退出？y/n")
                if 'y' in code.lower() or 'Y' in code.lower():
                    sys.exit(0)
                else:
                    continue
            except Exception as e:
                print(e)
        return True

    def __init__(self, logger_):

        Check.main()
        self.logger = logger_
        self.select = None
        self.download_url = None
        self.range = None
        self.downargs = {}
        self.Class_Config = SetConfig()
        self.Class_Driver = RunDriver(logger_)
        self.Class_Novel = None
        self.Class_Save = Save(logger_)
        self.Class_Qidian = Qidian(logger_, self.Class_Config, self.Class_Driver)
        self.Class_Fanqie = Fanqie(logger_, self.Class_Config, self.Class_Driver)
        self.Class_Biquge = Biquge(logger_, self.Class_Config, self.Class_Driver)
        self.Class_Novel = None
        return


# 创建日志记录器
# 作者：太多需要记录的日志了，有一点死了……
logger = logging.getLogger("auto_logger")
logger.setLevel(logging.DEBUG)

# 创建日志目录
log_dir = os.path.join(os.getenv("Temp"), "logs")
os.makedirs(log_dir, exist_ok=True)

# 文件处理器 - 按日期分割日志
file_handler = logging.FileHandler(
    filename=f"{log_dir}/{datetime.now().strftime('%Y-%m-%d')}.log",
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 日志格式
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)-8s] [%(funcName)-20s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
print(f"""
作者：Canyang2008
项目地址：https://github.com/canyang2008/NovelDownloader
检查配置中……{Fore.YELLOW}注：格式化操作是删除data/Local文件夹再次运行即可\n\n""")
sys.excepthook = global_exception_handler  # 设置全局异常处理器
downloader = NovelDownloader(logger)
downloader.func()  # 功能
