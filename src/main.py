import copy
import io
import json
import logging
import os
import re
import shlex
import sys
import time
from logging.handlers import TimedRotatingFileHandler
import winsound
from tqdm import tqdm
from Check import Check
from Fanqie import Fanqie
from GetHtml import GetHtml
from Qidian import Qidian
from RunDriver import RunDriver
from Save import Save
from SetConfig import SetConfig


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
        for group in self.Class_Config.url_config[self.Class_Config.Main_user].keys():
            if self.download_url in self.Class_Config.url_config[self.Class_Config.Main_user][group].keys():
                config = self.Class_Config.url_config[self.Class_Config.Main_user][group][self.download_url]
                json_path = config['Save_method']['json']['dir'] + '\\' + config["Name"] + '.json'
                if not os.path.exists(json_path):
                    print('json被移动或不存在')
                else:
                    with open(json_path, encoding='utf-8') as f:
                        self.Class_Novel.novel = json.load(f)
                    self.Class_Novel.down_title_list = [title for title in self.Class_Novel.down_title_list if
                                                        title not in self.Class_Novel.novel['chapters'].keys() or not
                                                        self.Class_Novel.novel['chapters'][title]['integrity']]
                    all_title_url = dict(
                        zip(self.Class_Novel.all_title_list, self.Class_Novel.all_url_list))  # 使用字典存储章节标题和链接
                    self.Class_Novel.down_url_list = [all_title_url[title] for title in
                                                      self.Class_Novel.down_title_list]
                    return True
        return False

    def load_downargs(self, downargs: str):

        # 使用shlex智能分割字符串（处理引号/空格）
        tokens = shlex.split(downargs.replace('=', ' '))
        tokens.insert(0, 'url')
        tokens = [i.replace('-', '') for i in tokens]

        if len(tokens) % 2 == 1:
            tokens.pop(0)
        it = iter(tokens)
        self.downargs = dict(zip(it, it))
        self.downargs = {k.lower(): v for k, v in self.downargs.items()}  # 键统一用小写

        url = self.downargs.get('url', None)
        self.logger.debug(f"Main:[ARGS]:原始的download_url:{url}")
        referer = re.search(r'https://?([^/]+)', url).group(1)
        self.logger.info(f"Main:[INFO]:referer:{referer}")
        url = re.search(r'[^?]+', url).group(0)
        if 'https://changdunovel.com/wap/' in url:  # 处理番茄小说的分享链接
            url = re.sub(r'^(\s*)\S+',
                         'https://fanqienovel.com/page/' + re.search(r"book_id=([^&]+)", url).group(1),
                         url)
        self.logger.info(f"Main:[ARGS]:已处理的download_url:{url}")
        if 'fanqienovel.com' in referer:
            self.Class_Novel = self.Class_Fanqie
            self.logger.info("Main:[INFO]:类Class_Novel已成功替换为类Class_Fanqie")
        elif 'qidian.com' in referer:
            self.Class_Novel = self.Class_Qidian
            self.logger.info("Main:[INFO]:类Class_Novel已成功替换为类Class_Qidian")
        else:
            print('不支持该网站，请检查链接')
            return False

        self.download_url = url
        self.Class_Config.set_url_config(url)  # 设置url的配置
        self.logger.info("Main:[INFO]:UrlConfig设置成功")
        self.Class_Config.Group = self.downargs.get('group', self.Class_Config.Group)
        self.range = self.downargs.get('range', None)
        self.novel_update = self.downargs.get('update', False)
        if self.novel_update and not self.novel_update.lower().startswith('f'):
            self.novel_update = True
        return self

    def download_novel(self, download_url):
        self.RunDriver.config(self.Class_Config)
        self.logger.info("Main:[INFO]:Webdriver开始配置")
        driver = self.RunDriver.run()  # 获取webdriver
        self.logger.info("Main:[INFO]:Webdriver启动")
        if driver:
            self.logger.info("Main:[INFO]:Webdriver启动成功")
            self.logger.info("Main:[INFO]:开始获取源码")
            soup = self.Class_GetHtml.get(download_url, driver, self.Class_Config.Wait_time)  # 获取soup
            self.Class_Novel.getpage(download_url, soup)  # 获取小说目录页
            self.logger.info("Main:[INFO]:成功获取小说目录页")
            if self.novel_update:
                self.update()
            if self.range:
                self.logger.info(f"Main:[INFO]:范围格式化中:{self.range}")
                self.range = range_split(self.range, len(self.Class_Novel.down_title_list))
                self.Class_Novel.down_title_list = [self.Class_Novel.down_title_list[i - 1] for i in self.range]
                self.Class_Novel.down_url_list = [self.Class_Novel.down_url_list[i - 1] for i in self.range]
                self.logger.info(f"Main:[INFO]:范围格式化成功:{self.range}")

            self.Class_Save.config(self.Class_Novel, self.Class_Config)
            self.logger.info("Main:[INFO]:保存小说的配置成功")
            with tqdm(total=len(self.Class_Novel.down_title_list),
                      desc=self.Class_Novel.novel['info']['name']) as down_progress:
                try:
                    for title, url in zip(self.Class_Novel.down_title_list, self.Class_Novel.down_url_list):
                        soup = self.Class_GetHtml.get(url, driver, self.Class_Config.Wait_time)
                        self.Class_Novel.getnovel(title, url, soup)
                        self.logger.info(f"Main:[INFO]:获取标题: {title} 的章节成功")
                        if self.Class_Config.Save_method:
                            self.Class_Save.save(title=title)
                            self.logger.info("Main:[INFO]:小说保存成功")
                        down_progress.update(1)
                    # 更新阅读进度
                    driver.get(self.Class_Novel.pro_url)
                    if self.Class_Config.setting_config["Play_completion_sound"]:
                        winsound.MessageBeep(winsound.MB_OK)
                    return True
                except Exception as e:
                    print(e)
                    raise
        else:
            print("webdriver出现错误")
            return False

    def func(self, funct: str):
        if funct == 'DEBUG':
            download_url = self.load_downargs(
                "https://fanqienovel.com/page/7276384138653862966 --group=Default --update=True").download_url
            self.download_novel(download_url)
            return True
        while True:

            url_config = copy.deepcopy(self.Class_Config.url_config)
            urls_para = []
            urls = []
            for group in url_config[self.Class_Config.Main_user].keys():
                for url in url_config[self.Class_Config.Main_user][group].keys():
                    name = url_config[self.Class_Config.Main_user][group][url]['Name']
                    urls.append(url)
                    urls_para.append((group, name, url))

            print(f"\n当前账户：{self.Class_Config.Main_user}    当前分组：{self.Class_Config.Main_group}")
            self.select = input(
                """
请输入功能:
1.更新小说：
2.下载：
3.批量下载：
4.指定章节下载:
5.设置:
""").strip()
            match self.select:
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
                    self.download_novel(self.download_url)
                case "3":
                    print(
                        '''将打开urls.txt,请在文件中输入小说链接，一行一个。\
                        输入完成后请保存并关闭文件，然后按 Enter 键继续...''')
                    time.sleep(0.5)
                    os.startfile('data\\Record\\urls.txt')
                    input()
                    with open('data\\Record\\urls.txt', 'r', encoding='utf-8') as f:
                        for line in f:
                            if not line:
                                continue
                            self.download_url = self.load_downargs(line).download_url
                            self.download_novel(self.download_url)

                case "4":
                    para = input('请输入小说链接(参数):')
                    if not para:
                        continue
                    if 'range' in para:
                        self.download_url = self.load_downargs(para).download_url
                    else:
                        novel_range = input('请输入章节范围(如1-3,5,7-9):')
                        para = para.strip() + ' ' + novel_range.strip()
                        self.download_url = self.load_downargs(para).download_url
                    self.download_novel(self.download_url)

                case "5":
                    choice = input(
                        """
1.账户操作：
2.分组内操作：
3.默认值修改:
""")
                    match choice:
                        case '1':
                            users = self.Class_Config.setting_config['Users']
                            for user_idx in range(1, len(users) + 1):
                                print(f"{user_idx}.{users[user_idx - 1]}")
                            print(f"当前账户:{self.Class_Config.Main_user}")
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
                                            self.Class_Config.save_config()
                                            self.Class_Config.Main_user = users[option - 1]
                                            print(f"账户切换成功({users[option - 1]})")
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
                                            self.Class_Config.setting_config['Users'].append(user_input)
                                            self.Class_Config.setting_config["User"] = user_input
                                            self.Class_Config.save_config()
                                            self.Class_Config.Main_user = user_input
                                            print(f"账户已创建成功({user_input})")
                                            break

                                case "3":
                                    print("请选择需删除的账户(数字):", end="")
                                    option = input().strip()
                                    if not option or 'r' in option.lower():
                                        print("已退出..")
                                    if re.match(r"\d+", option.strip()):
                                        option = int(option)
                                        del_user = self.Class_Config.setting_config["Users"].pop(option - 1)
                                        if del_user == self.Class_Config.Main_user:
                                            self.Class_Config.setting_config["User"] = users[0]
                                            self.Class_Config.Main_user = users[0]
                                            self.Class_Config.save_config()
                                            print(f"账户 {del_user} 已删除成功({self.Class_Config.Main_user})")
                                        self.Class_Config.save_config()

                        case '2':
                            groups = list(self.Class_Config.url_config[self.Class_Config.Main_user].keys())
                            for group_idx in range(1, len(groups) + 1):
                                print(f"{group_idx}.{groups[group_idx - 1]}")
                            print(f"当前分组:{self.Class_Config.Main_group}")
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
                                            self.Class_Config.save_config()
                                            self.Class_Config.Main_group = groups[option - 1]
                                            print(f"分组切换成功({groups[option - 1]})")
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
                                            self.Class_Config.setting_config["Group"] = group_input
                                            self.Class_Config.url_config[self.Class_Config.Main_user][group_input] = {}
                                            self.Class_Config.save_config()
                                            self.Class_Config.Main_group = group_input
                                            print(f"分组已创建成功({group_input})")
                                            break

                                case "3":
                                    print("请选择需删除的分组(数字):", end="")
                                    option = input().strip()
                                    if not option or 'r' in option.lower():
                                        print("已退出..")
                                    if re.match(r"\d+", option.strip()):
                                        option = int(option)
                                        del_group = self.Class_Config.url_config[self.Class_Config.Main_user].pop(
                                            groups[option - 1])
                                        if del_group == self.Class_Config.Main_group:
                                            self.Class_Config.url_config[self.Class_Config.Main_user] = groups[0]
                                            self.Class_Config.Main_group = groups[0]
                                            self.Class_Config.save_config()
                                            print(f"分组 {del_group} 已删除成功({self.Class_Config.Main_group})")
                                        self.Class_Config.save_config()

                        case '3':
                            print('暂未实现..')
                            continue

        return True


    def __init__(self):

        self.novel_update = None
        self.select = None
        self.download_url = None
        self.range = None
        self.downargs = {}
        # 1. 创建日志记录器
        self.logger = logging.getLogger("MAIN")
        self.logger.setLevel(logging.DEBUG)  # 设置记录器级别

        # 2. 创建处理器（控制台+文件）
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # 控制台只显示WARNING以上级别

        # 文件处理器（自动按天分割日志）
        file_handler = TimedRotatingFileHandler(
            filename='data\\log\\main.log',
            when='midnight',  # 每天午夜分割
            backupCount=7,  # 保留7天日志
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)

        # 3. 设置日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)-8s %(name)-12s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 4. 将处理器添加到记录器
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.Class_Config = SetConfig(self.logger)
        self.Class_Check = Check(self.logger)
        self.RunDriver = RunDriver(self.logger)
        self.Class_GetHtml = GetHtml(self.logger, self.RunDriver)
        self.Class_Save = Save(self.logger)
        self.Class_Qidian = Qidian(self.logger)
        self.Class_Fanqie = Fanqie(self.logger)
        self.Class_Novel = None

        return


if sys.stdout.encoding != 'UTF-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'UTF-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
downloader = NovelDownloader().func("DEBUG  ")
