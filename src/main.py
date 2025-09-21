# -*- coding: utf-8 -*-
import copy
import faulthandler
import json
import logging
import os
import re
import shlex
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import winsound
from bs4 import BeautifulSoup
from colorama import init, Fore
from tqdm import tqdm

import Check
from Check import Check as CCheck
from Fanqie import Fanqie
from GetHtml import GetHtml
from Qidian import Qidian
from RunDriver import RunDriver
from Save import Save
from SetConfig import SetConfig

faulthandler.enable()
init(autoreset=True)


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


def range_split(deal_range, total_list):
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
        file_name = self.Class_Config.mems[self.Class_Config.Group][self.download_url] + '.json'
        json_path = Path(self.Class_Config.Base_dir) / file_name
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

    def load_downargs(self, downargs: str):

        # 使用shlex智能分割字符串
        basic_tokens = shlex.split(downargs)
        basic_tokens.insert(0, 'url')
        tokens = basic_tokens[:2]  # 避免url误入其中
        for token in basic_tokens[2:]:
            token = re.sub(r"^-{1,2}", '', token)
            args = token.lower().split('=')
            tokens.extend([args[0], args[1]])
        it = iter(tokens)
        # 转变为键值对
        self.downargs = dict(zip(it, it))
        self.downargs = {k.lower(): v for k, v in self.downargs.items()}  # 键统一用小写
        url = self.downargs.get('url')
        if 'https://changdunovel.com/wap/' in url:  # 处理番茄小说的分享链接
            book_id = re.search(r"book_id=(\d+)", url).group(1)
            url = 'https://fanqienovel.com/page/' + book_id
        self.downargs['url'] = url.split('?')[0]  # 不带参数的url
        url = url.split('?')[0]  # 不带参数的url
        if 'fanqienovel.com' in url:
            self.Class_Novel = self.Class_Fanqie
        elif 'qidian.com' in url:
            self.Class_Novel = self.Class_Qidian
        else:
            print('不支持该网站，请检查链接')
            return False

        self.download_url = url
        self.Class_Config.Group = self.downargs.get('group', self.Class_Config.Group)
        self.range = self.downargs.get('range', None)
        self.novel_update = self.downargs.get('update', False)
        self.Class_Config.Headless = self.downargs.get('headless', False)
        if self.novel_update and not self.novel_update.lower().startswith('f'):  # 当update有值且不以f开头时默认为True
            self.novel_update = True
        self.Class_Config.set_config(url, self.novel_update)  # 设置url的配置
        return self

    def download_novel(self, download_url):
        if self.Class_Config.Get_mode == 0:
            self.Class_Driver.config(user_data_dir=self.Class_Config.User_data_dir, port=self.Class_Config.Port,
                                     headless=self.Class_Config.Headless)
            self.Class_Driver.run()
        if not self.Class_Novel.get_page(download_url):
            return False
        if self.novel_update:
            self.update()  # 获取需更新小说标题及链接
            self.Class_Save.config(self.Class_Novel, self.Class_Config)  # 初始化保存配置
            self.Class_Save.save(full_save=True)  # 覆写模式保存
        if self.range:
            self.range = range_split(self.range, len(self.Class_Novel.down_title_list))  # 分割范围成连续数字列表
            self.Class_Novel.down_title_list = [self.Class_Novel.down_title_list[i - 1] for i in self.range]
            self.Class_Novel.down_url_list = [self.Class_Novel.down_url_list[i - 1] for i in self.range]
        self.Class_Save.config(self.Class_Novel, self.Class_Config)  # 初始化保存配置
        with tqdm(total=len(self.Class_Novel.down_title_list),
                  desc=self.Class_Novel.novel['info']['name']) as down_progress:
            index = 0
            try:
                for title, url in zip(self.Class_Novel.down_title_list, self.Class_Novel.down_url_list):
                    index += 1
                    if not self.Class_Novel.download(title, url, index, self.download_url): return False
                    if self.Class_Config.Save_method: pass
                    self.Class_Save.save(title=title)  # 保存
                    down_progress.update(1)
                if self.Class_Config.User_config["Play_completion_sound"]:
                    winsound.MessageBeep(winsound.MB_OK)  # 播放完成音
                down_progress.update(1)
                return True
            except KeyboardInterrupt:
                print("已退出..")

    def func(self):

        while True:
            self.Class_Config.load()
            try:
                saved_mems = copy.deepcopy(self.Class_Config.mems)
                urls_para = []
                urls = []  # 所有已保存的url
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
""").strip()
                match self.select:  # 嵌套严重，被绕晕了..
                    case '0':
                        option = input("""请选择网站：
1.番茄：
2.起点：
3.(新)笔趣阁：
""")
                        if not option and re.match(r"^\d$", option):
                            print('输入错误')
                            continue
                        self.Class_Driver.config(user_data_dir=self.Class_Config.User_data_dir,
                                                 port=self.Class_Config.Port, headless=False)
                        tab = self.Class_Driver.run()
                        match option:
                            case '1':
                                tab.get("https://fanqienovel.com/main/writer/login")
                                input("登录后按下任意键继续..")
                                soup = BeautifulSoup(tab.raw_data)
                                self.Class_Fanqie.user_state_for_html(soup)
                                match self.Class_Fanqie.user_state_code:
                                    case -1:
                                        print(f"{Fore.YELLOW}番茄账号未登录，下载的小说将不完整")
                                        self.Class_Config.User_config['Browser']['State']['Fanqie'] = -1
                                    case 0:
                                        print(f"{Fore.YELLOW}番茄账号已登录但无vip，下载的小说将不完整")
                                        self.Class_Config.User_config['Browser']['State']['Fanqie'] = 0
                                    case 1:
                                        print(f"{Fore.GREEN}番茄账号已登录且有vip")
                                        self.Class_Config.User_config['Browser']['State']['Fanqie'] = 1
                                self.Class_Config.save_config(1)

                            case '2':
                                tab.get("https://fanqienovel.com/main/writer/login")
                                input("登录后按下任意键继续..")

                            case '3':
                                print("暂未实现")


                    case "1":
                        for sequence in range(len(urls_para)):  print(
                            f'{sequence + 1}.群组：{urls_para[sequence][0]} 小说名：{urls_para[sequence][1]}')
                        choice = input('请输入数字或范围（如1-3,5,7-9；last:3；all）')
                        if not choice:
                            print('输入错误')
                            continue
                        update_range = range_split(choice, len(urls_para))
                        for index in update_range:
                            self.download_url = urls_para[index - 1][2]
                            self.download_url += ' --update=True'
                            self.download_url = self.load_downargs(self.download_url).download_url
                            self.download_novel(self.download_url)

                    case "2":
                        para = input('请输入小说链接(参数):')
                        if not para:
                            print('输入错误')
                            continue
                        self.download_url = self.load_downargs(para).download_url
                        if self.download_url in urls:
                            print("当前链接存在，自动更新中…")
                            self.download_url += ' --update=True'
                            self.download_url = self.load_downargs(para).download_url
                        self.download_novel(self.download_url)

                    case "3":
                        print(
                            """将打开urls.txt,请在文件中输入小说链接，一行一个。\
                            输入完成后请保存并关闭文件，然后按 Enter 键继续...""")
                        time.sleep(0.5)
                        os.startfile('data\\Local\\urls.txt')
                        input()
                        with open('data\\Local\\urls.txt', 'r', encoding='utf-8') as f_:
                            for line in f_:
                                if not line:
                                    continue
                                self.download_url = self.load_downargs(line).download_url
                                if self.download_url in urls:
                                    print("当前链接存在，自动更新中…")
                                    self.novel_update = True
                                self.download_novel(self.download_url)

                    case "4":
                        para = input('请输入小说链接(参数):')
                        if not para:
                            continue
                        if 'range' in para:
                            self.download_url = self.load_downargs(para).download_url
                        else:
                            novel_range = input('请输入章节范围(如1-3,5,7-9):')
                            para = para.strip() + ' --range=' + novel_range.strip()
                            self.download_url = self.load_downargs(para).download_url
                        self.download_novel(self.download_url)

                    case "5":
                        choice = input(
                            """
1.账户操作：
2.分组内操作：
""")
                        match choice:
                            case '1':
                                users = list(self.Class_Config.User_manage['USERS'].keys())
                                for user_idx in range(1, len(users) + 1):
                                    print(f"{user_idx}.{users[user_idx - 1]}")
                                print(f"当前账户:{Fore.LIGHTBLUE_EX}{self.Class_Config.USER}")
                                print("如果退出请按r键")
                                choice = input("1.账户切换    2.账户创建    3.账户删除").strip()
                                match choice:
                                    case "1":
                                        print("请选择账户(数字):")
                                        while True:
                                            option = input().strip()
                                            if not option or 'r' in option.lower():
                                                print("已退出..")
                                                break
                                            if re.match(r"\d+", option.strip()):
                                                option = int(option)
                                                self.Class_Config.User_manage["USER"] = users[option - 1]
                                                self.Class_Config.save_config(2)
                                                self.Class_Config.load()
                                                print(f"账户切换成功({self.Class_Config.USER})")
                                                break
                                            else:
                                                print("请重新输入:")
                                                continue

                                    case "2":
                                        while True:
                                            user_input = input("请输入账户名(前后不允许空格):").strip()
                                            if not user_input or 'r' in user_input.lower():
                                                print("不创建账户，已退出..")
                                                break
                                            if user_input in users:
                                                print("账户已存在，请重新创建..")
                                                continue
                                            else:
                                                self.Class_Config.set_new_userconfig(user_input)
                                                print(f"账户已创建成功({self.Class_Config.USER})")
                                                break

                                    case "3":
                                        option = input("请选择需删除的账户(数字):").strip()
                                        if not option or 'r' in option.lower():
                                            print("已退出..")
                                        if re.match(r"\d+", option.strip()):
                                            option = int(option)
                                            del_user = self.Class_Config.User_manage["USERS"].pop(option - 1)
                                            if del_user == self.Class_Config.USER:
                                                self.Class_Config.User_manage["USER"] = users[0]
                                                self.Class_Config.save_config(2)
                                                self.Class_Config.load()
                                                print(f"账户 {del_user} 已删除成功({self.Class_Config.USER})")
                                            self.Class_Config.save_config()

                            case '2':
                                groups = list(self.Class_Config.mems.keys())
                                for group_idx in range(1, len(groups) + 1):
                                    print(f"{group_idx}.{groups[group_idx - 1]}")
                                print(f"当前分组:{self.Class_Config.GROUP}")
                                print("如果退出请按r键")
                                option = input("1.分组切换    2.分组创建    3.分组删除").strip()
                                match option:
                                    case "1":
                                        print("请选择分组(数字):")
                                        while True:
                                            option = input().strip()
                                            if not option or 'r' in option.lower():
                                                print("已退出..")
                                                break
                                            if re.match(r"\d+", option.strip()):
                                                option = int(option)
                                                self.Class_Config.User_config['Group'] = groups[option - 1]
                                                self.Class_Config.save_config(1)
                                                self.Class_Config.load()
                                                print(f"分组切换成功({self.Class_Config.GROUP})")
                                                break
                                            else:
                                                print("请重新输入:")
                                                continue

                                    case "2":
                                        while True:
                                            group_input = input("请输入分组名(前后不允许空格):").strip()
                                            if not group_input or 'r' in group_input.lower():
                                                print("不创建分组，已退出..")
                                                break
                                            if group_input in groups:
                                                print("分组已存在，请重新创建..")
                                                continue
                                            else:
                                                self.Class_Config.User_config["Group"] = group_input
                                                self.Class_Config.mems[group_input] = {}
                                                self.Class_Config.save_config(0)
                                                self.Class_Config.save_config(1)
                                                self.Class_Config.load()
                                                print(f"分组已创建成功({self.Class_Config.GROUP})")
                                                break

                                    case "3":
                                        print("请选择需删除的分组(数字):", end="")
                                        option = input().strip()
                                        if not option or 'r' in option.lower():
                                            print("已退出..")
                                        if re.match(r"\d+", option.strip()):
                                            option = int(option)
                                            del_group = groups[option - 1]
                                            self.Class_Config.mems.pop(del_group)
                                            if del_group == self.Class_Config.GROUP:
                                                self.Class_Config.User_config['Group'] = groups[0]
                                            self.Class_Config.save_config(0)
                                            self.Class_Config.save_config(1)
                                            self.Class_Config.load()
                                            print(f"分组 {del_group} 已删除成功({self.Class_Config.GROUP})")


            except KeyboardInterrupt:
                code = input("是否退出？y/n")
                if 'y' in code.lower() or 'Y' in code.lower():
                    sys.exit(0)
                else:
                    continue
        return True

    def __init__(self, logger_):

        self.logger = logger_
        self.novel_update = None
        self.select = None
        self.download_url = None
        self.range = None
        self.downargs = {}
        self.Class_Config = SetConfig()
        self.Class_Check = CCheck()
        self.Class_Driver = RunDriver(logger_)
        self.Class_Novel = GetHtml(self.Class_Driver, self.Class_Config.User_config['Play_completion_sound'], logger_)
        self.Class_Save = Save(logger_)
        self.Class_Qidian = Qidian(logger_, self.Class_Novel, self.Class_Config, self.Class_Driver)
        self.Class_Fanqie = Fanqie(logger_, self.Class_Novel, self.Class_Config, self.Class_Driver)
        self.Class_Novel = None

        return


# 创建日志记录器
# 作者：太多需要记录的日志了，有一点死了……下周末再弄吧
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
如果在使用过程中想反馈，欢迎参与讨论:
    QQ：765857967    issues：https://github.com/canyang2008/NovelDownloader/issues/1\n
检查配置中……{Fore.YELLOW}注：格式化操作是删除data/Local文件夹再次运行即可\n\n""")
if os.path.exists("data/Record/UrlConfig.json"):
    import transform

    transform.init()
if not os.path.exists("data/Local"):
    print(f"{Fore.YELLOW}重置中")
    Check.init()
sys.excepthook = global_exception_handler  # 设置全局异常处理器
downloader = NovelDownloader(logger)
downloader.func()  # 功能
