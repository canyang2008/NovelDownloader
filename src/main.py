# -*- coding: utf-8 -*-
import copy
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
LASTEST_USERCONFIG_VERSION = '1.1.4'    # 最后一次版本配置更新
template_userconfig = \
{
"Version": "1.1.4",
"User_name": "Default",
"Group": "Default",
"README": "",
"Play_completion_sound": False,
"Get_mode": 0,
"Browser": {
  "State": {
    "Fanqie": -1,
    "Qidian": 0,
    "Bqg128": 0
  },
  "Timeout": 10,
  "Max_retry": 3,
  "Interval": 2,
  "Delay": [
    1,
    1.5
  ],
  "Port": 9445,
  "Headless": False,
  "path": ""
},
"Api": {
  "Fanqie": {
    "Option": "oiapi",
    "oiapi": {
      "Max_retry": 3,
      "Timeout": 10,
      "Interval": 2,
      "Delay": [
        1,
        3
      ],
      "Key": ""
    }
  }
},
"Save_method": {
  "json": {
    "enable": True,
    "name": "name_default",
    "dir": "data\\Bookstore\\<User>\\<Group>\\<Name>",
    "img_dir": "data\\Bookstore\\<User>\\<Group>\\<Name>\\Img"
  },
  "txt": {
    "enable": True,
    "name": "name_default",
    "dir": "data\\Bookstore\\<User>\\<Group>\\<Name>",
    "gap": 0,
    "max_filesize": -1
  },
  "html": {
    "enable": True,
    "name": "name_default",
    "dir": "data\\Bookstore\\<User>\\<Group>\\<Name>",
    "one_file": True
  }
},
  "Requests": {
    "Fanqie": {
      "Max_retry": 3,
      "Timeout": 10,
      "Interval": 2,
      "Delay": [
        1,
        3
      ],
      "Cookie": ""
    },
    "Qidian": {
      "Max_retry": 3,
      "Timeout": 10,
      "Interval": 2,
      "Delay": [
        1,
        3
      ],
      "Cookie": ""
    },
    "Biquge": {
      "Max_retry": 3,
      "Timeout": 10,
      "Interval": 2,
      "Delay": [
        1,
        3
      ],
      "Cookie": ""
    }
  },
  "Backup": {
    "Auto": False,
    "Auto_save_method": "T:86400",
    "Dir": "C:\\\\",
    "Name": "Novel_backup <User> <T:'%Y-%m-%d'>.zip",
    "Last_time": -1,
    "Pop_up_folder": True
  },
    "Unprocess": []
}


def mode_config_modify(choice: str, mode_user_config: dict) -> dict | bool:
    if re.match('^[1-6]$', choice.strip()):
        choice = int(choice)
        match choice:
            case 1:
                timeout_input = input("请输入超时时间")
                if re.match('^\d+$', timeout_input.strip()):
                    mode_user_config['Timeout'] = int(timeout_input)
                    return mode_user_config
            case 2:
                max_retry_input = input("请输入最大重试次数")
                if re.match('^\d+$', max_retry_input.strip()):
                    mode_user_config['Max_retry'] = int(max_retry_input)
                    return mode_user_config
            case 3:
                interval_input = input("请输入最大重试间隔")
                if re.match('^\d+$', interval_input.strip()):
                    mode_user_config['Interval'] = int(interval_input)
                    return mode_user_config
            case 4:
                delay_input = input("请输入上限 下限，用空格隔开")
                if not re.match('^(\d+) (\d+)$', delay_input.strip()):
                    return False
                delay_input_list = delay_input.split()
                new_delay = []
                if len(delay_input_list) == 2 and int(delay_input_list[0]) <= int(delay_input_list[1]):
                    new_delay[0] = int(delay_input_list[0])
                    new_delay[1] = int(delay_input_list[1])
                    mode_user_config['Delay'] = new_delay
                    return mode_user_config
    else:
        print("输入错误")
        return False


def setting(option: str, user_config: dict) -> dict | bool:
    """设置配置
1.获取模式
2.Chrome设置
3.API设置
4.Requests设置
5.保存方式设置"""
    match option:
        case '1':
            print("1.Chrome模式   2.API模式(仅番茄)     3.Requests模式(开发中)")
            current_mode = user_config['Get_mode']
            match current_mode:
                case 1:
                    print("当前模式：Chrome")
                case 2:
                    print("当前模式：API")
                case 3:
                    print("当前模式：Requests")
            mode_option = input("是否切换?(1|2|3/n)")
            if re.match('^[1-3]$', mode_option.strip()):
                mode = int(mode_option) - 1
                user_config['Get_mode'] = mode
                return user_config

        case '2':
            mode_user_config = user_config['Browser']
            timeout = mode_user_config["Timeout"]
            max_retry = mode_user_config["Max_retry"]
            interval = mode_user_config["Interval"]
            delay = mode_user_config['Delay']
            delay_str = f"上限：{delay[0]}s 下限：{delay[1]}s"
            port = mode_user_config['Port']
            headless = mode_user_config['Headless']
            print(f'''
1.超时时间(当前:{timeout}s)
2.最大重试次数(当前:{max_retry})
3.重试时间间隔(当前:{interval}s)
4.延迟(当前:{delay_str})
5.Chrome端口号(当前:{port})
6.无头模式(当前:{headless})'''
                  )
            choice = input("请选择修改或退出(n)")
            if re.match('^[1-4]$', choice.strip()):
                mode_user_config = mode_config_modify(choice, mode_user_config)
                user_config['Browser'].update(mode_user_config)
                return user_config
            elif re.match('^[56]$', choice.strip()):
                match choice:
                    case '5':
                        port = input("请输入端口号")
                        if re.match('^\d+$', port.strip()):
                            mode_user_config['Port'] = int(port)
                            user_config['Browser'].update(mode_user_config)
                            return user_config
                    case '6':
                        cho = input("是否启用无头模式(y/n)")
                        if cho.strip() == 'y':
                            headless = True
                            mode_user_config['Headless'] = headless
                            user_config['Browser'].update(mode_user_config)
                            return user_config
        case '3':
            mode_user_config = user_config['Api']['Fanqie']['oiapi']
            print("当前API:oiapi")
            timeout = mode_user_config["Timeout"]
            max_retry = mode_user_config["Max_retry"]
            interval = mode_user_config["Interval"]
            delay = mode_user_config['Delay']
            delay_str = f"上限：{delay[0]}s 下限：{delay[1]}s"
            api_key = mode_user_config['Key']
            print(f'''
1.超时时间(当前:{timeout}s)
2.最大重试次数(当前:{max_retry})
3.重试时间间隔(当前:{interval}s)
4.延迟(当前:{delay_str})
5.ApiKey(当前:{api_key})'''
                  )
            choice = input("请选择修改或退出(n)")
            if re.match('^[1-4]$', choice.strip()):
                mode_user_config = mode_config_modify(choice, mode_user_config)
                user_config['Api']['Fanqie']['oiapi'].update(mode_user_config)
                return user_config
            elif choice.strip() == '5':
                new_api_key = input("请输入ApiKey")
                mode_user_config['Key'] = new_api_key
                user_config['Api']['Fanqie']['oiapi'].update(mode_user_config)
                return user_config
            else:
                pass
        case '4':
            platform_choice = input("""请输入平台：
1.番茄
2.起点
3.笔趣阁

""")
            platform_list = ['Fanqie', "Qidian", "Biquge"]
            if re.match('^[1-3]$', platform_choice.strip()):
                platform = platform_list[int(platform_choice) - 1]
            else:
                print("输入错误")
                return False
            mode_user_config = user_config['Requests'][platform]
            timeout = mode_user_config["Timeout"]
            max_retry = mode_user_config["Max_retry"]
            interval = mode_user_config["Interval"]
            delay = mode_user_config['Delay']
            delay_str = f"上限：{delay[0]}s 下限：{delay[1]}s"
            cookie = mode_user_config['Cookie']
            print("当前Requests配置:")
            print(f'''
1.超时时间(当前:{timeout}s)
2.最大重试次数(当前:{max_retry})
3.重试时间间隔(当前:{interval}s)
4.延迟(当前:{delay_str})
5.Cookie:(当前:{cookie})
'''
                  )
            choice = input("请选择修改或退出(n)")
            if re.match('^[1-4]$', choice.strip()):
                mode_user_config = mode_config_modify(choice, mode_user_config)
                user_config['Requests'][platform].update(mode_user_config)
                return user_config
            elif choice.strip() == '5':
                new_cookie = input("请输入Cookie")
                mode_user_config['Cookie'] = new_cookie
                user_config['Requests'][platform].update(mode_user_config)
                return user_config
            """保存方式设置"""
        case '5':
            save_method = user_config['Save_method']
            print()
            total = 0
            for index in range(len(list(save_method.keys()))):
                print(f"{index + 1}:{list(save_method.keys())[index]}")
                total += 1
            choice = input("\n请选择文件格式:")
            if re.match('^\d$', choice.strip()):
                file_format = list(save_method.keys())[int(choice) - 1]
                match file_format:
                    case 'json':
                        file_method = save_method[file_format]
                        enable = file_method.get('enable', True)
                        name = file_method.get('name', "name_default")
                        name_str = name if name != "name_default" else "以小说名称保存"
                        save_dir = file_method.get('dir', "data\Bookstore\<User>\<Group>\<Name>")
                        img_save_dir = file_method.get("img_dir", "data\\Bookstore\\<User>\\<Group>\\<Name>\\Img")
                        print("当前json保存配置:\n")
                        print(f"""
1.是否以json保存(当前:{enable})
2.文件名称(当前:{name_str})
3.保存目录(当前：{save_dir})
4.图片保存目录(当前:{img_save_dir})\n
""")
                        cho = input("请选择或退出(n)")
                        match cho.strip():
                            case '1':
                                enable_choice = input("是否以json保存(y/n)")
                                if enable_choice.strip() == 'y':
                                    user_config['Save_method']['json']['enable'] = True
                                    return user_config
                                elif enable_choice.strip() == 'n':
                                    user_config['Save_method']['json']['enable'] = False
                                    return user_config
                            case '2':
                                new_name = input("请输入文件名称或退出(n)")
                                if new_name.strip() == 'n':
                                    pass
                                else:
                                    user_config['Save_method']['json']['name'] = new_name
                                    return user_config
                            case '3':
                                print(
                                    '特殊名称\n"<User>":替换为当前用户名称\n"<Group>":替换为当前用户\n"<Name>":替换为当前小说名称')
                                new_dir = input("请输入目录或退出(n)(可输入特殊名称):")
                                if new_dir.strip() == 'n':
                                    pass
                                else:
                                    user_config['Save_method']['json']['dir'] = new_dir
                                    return user_config
                            case '4':
                                print(
                                    '特殊名称\n"<User>":替换为当前用户名称\n"<Group>":替换为当前用户\n"<Name>":替换为当前小说名称')
                                new_img_dir = input("请输入图片保存目录或退出(n)(可输入特殊名称):")
                                if new_img_dir.strip() == 'n':
                                    pass
                                else:
                                    user_config['Save_method']['json']['img_dir'] = new_img_dir
                                    return user_config

                    case 'txt':
                        file_method = save_method[file_format]
                        enable = file_method.get('enable', True)
                        name = file_method.get('name', "name_default")
                        name_str = name if name != "name_default" else "以小说名称保存"
                        save_dir = file_method.get('dir', "data\Bookstore\<User>\<Group>\<Name>")
                        gap = file_method.get('gap', 0)
                        max_filesize = file_method.get('max_filesize', -1)
                        print("当前txt保存配置:\n")
                        print(f"""
1.是否以txt保存(当前:{enable})
2.文件名称(当前:{name_str})
3.保存目录(当前：{save_dir})
4.分块(当前:{gap})
5.最大文件大小(当前：{max_filesize})\n
""")
                        cho = input("请选择或退出(n)")
                        match cho.strip():
                            case '1':
                                enable_choice = input("是否以txt保存(y/n)")
                                if enable_choice.strip() == 'y':
                                    user_config['Save_method']['txt']['enable'] = True
                                    return user_config
                                elif enable_choice.strip() == 'n':
                                    user_config['Save_method']['txt']['enable'] = False
                                    return user_config
                            case '2':
                                new_name = input("请输入文件名称或退出(n)")
                                if new_name.strip() == 'n':
                                    pass
                                else:
                                    user_config['Save_method']['txt']['name'] = new_name
                                    return user_config
                            case '3':
                                print(
                                    '特殊名称\n"<User>":替换为当前用户名称\n"<Group>":替换为当前用户\n"<Name>":替换为当前小说名称')
                                new_dir = input("请输入目录或退出(n)(可输入特殊名称):")
                                if new_dir.strip() == 'n':
                                    pass
                                else:
                                    user_config['Save_method']['txt']['dir'] = new_dir
                                    return user_config
                            case '4':
                                new_gap = input("请输入分块或退出(n):")
                                if new_gap.strip() == 'n':
                                    pass
                                else:
                                    if re.match('^\d+$', new_gap.strip()):
                                        new_gap = int(new_gap)
                                        if new_gap >= 0:
                                            user_config['Save_method']['txt']['gap'] = new_gap
                                            return user_config
                                        else:
                                            print("分块不能小于0")

                    case 'html':
                        file_method = save_method[file_format]
                        enable = file_method.get('enable', True)
                        name = file_method.get('name', "name_default")
                        name_str = name if name != "name_default" else "以小说名称保存"
                        save_dir = file_method.get('dir', "data\Bookstore\<User>\<Group>\<Name>")
                        print("当前txt保存配置:\n")
                        print(f"""
1.是否以html保存(当前:{enable})
2.文件名称(当前:{name_str})
3.保存目录(当前：{save_dir})
4.图片嵌入html\n
""")
                        cho = input("请选择或退出(n)")
                        match cho.strip():
                            case '1':
                                enable_choice = input("是否以html保存(y/n)")
                                if enable_choice.strip() == 'y':
                                    user_config['Save_method']['html']['enable'] = True
                                    return user_config
                                elif enable_choice.strip() == 'n':
                                    user_config['Save_method']['html']['enable'] = False
                                    return user_config
                            case '2':
                                new_name = input("请输入文件名称或退出(n)")
                                if new_name.strip() == 'n':
                                    pass
                                else:
                                    user_config['Save_method']['html']['name'] = new_name
                                    return user_config
                            case '3':
                                print(
                                    '特殊名称\n"<User>":替换为当前用户名称\n"<Group>":替换为当前用户\n"<Name>":替换为当前小说名称')
                                new_dir = input("请输入目录或退出(n)(可输入特殊名称):")
                                if new_dir.strip() == 'n':
                                    pass
                                else:
                                    user_config['Save_method']['html']['dir'] = new_dir
                                    return user_config
                            case '4':
                                inner_choice = input("图片是否嵌入(y/n)")
                                if inner_choice.strip() == 'y':
                                    user_config['Save_method']['html']['one_file'] = True
                                elif inner_choice.strip() == 'n':
                                    user_config['Save_method']['html']['one_file'] = False
                                else:
                                    pass
            else:
                pass
        case _:
            pass
    print("输入错误")
    return False


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


def backup(backup_config:dict, backup_item:dict, auto:bool = False) -> str | bool:
    backup_dir = backup_config.get('Dir', "C:\\")
    user = backup_item["USER"]
    backup_name = backup_config.get('Name', "Novel_backup <User> <T:'%Y-%m-%d'>.zip")
    backup_method_list = re.findall(r"<.+?>",backup_name)
    for backup_method in backup_method_list:
        if backup_method == '<User>':
            backup_name = backup_name.replace(backup_method, user)
        elif backup_method.startswith('<T:'):
            time_format = re.search(r"'(.+)'>",backup_method).group(1)
            if time_format:
                time_str = time.strftime(time_format, time.localtime(time.time()))
                backup_name = backup_name.replace(backup_method, time_str)
    backup_path = Path(backup_dir) / backup_name
    if not auto:
        pop_up_folder = backup_config.get('Pop_up_folder', True)
        if pop_up_folder:
            root = tk.Tk()
            root.withdraw()
            backup_path = filedialog.asksaveasfilename(initialfile=backup_name, filetypes=[("zip文件",'.zip'),("所有文件",".*")])
            root.destroy()
            if not backup_path:
                print("保存路径不能为空")
                return False

    backup_item = backup_item['USERS'][user]
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_STORED) as zipf:
        for path in backup_item.keys():
            if 'User_config_path' == path:
                zipf.write(backup_item['User_config_path'], "UserConfig.json")
            if "Base_dir" == path:
                for root, _, files in os.walk(backup_item[path]):
                    for file in files:
                        if file.endswith(".json"):
                            json_path = (os.path.join(backup_item["Base_dir"], file))
                            zipf.write(str(json_path), os.path.join('json', file))
    return backup_path

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
        file_name = self.Class_Config.mems[self.Class_Config.Group][self.download_url] + '.json'  # 需要读取的文件全名
        json_path = Path(self.Class_Config.Base_dir) / file_name  # 路径
        if not os.path.exists(json_path):
            print('json文件被移动或不存在')
        else:
            with open(json_path, "r", encoding='utf-8') as novel_f:
                read_data = json.load(novel_f)
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

        if 'https://changdunovel.com/wap/' in url:  # 处理番茄小说的分享链接
            book_id = re.search(r"book_id=(\d+)", url).group(1)
            url = 'https://fanqienovel.com/page/' + book_id
        if "https://magev6.if.qidian.com/h5/share" in url:  # 处理起点小说的分享链接
            book_id = re.search(r"bookld=(\d+)", url).group(1)
            url = 'https://www.qidian.com/book/' + book_id
        url = url.split('?')[0].strip()  # 不带参数的url
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
            self.Class_Save.save(None)  # 覆写模式保存
        if self.range:
            self.range = range_split(self.range, len(self.Class_Novel.down_title_list))  # 分割范围成连续数字列表
            self.Class_Novel.down_title_list = [self.Class_Novel.down_title_list[index - 1] for index in self.range]
            self.Class_Novel.down_url_list = [self.Class_Novel.down_url_list[index - 1] for index in self.range]
        self.Class_Save.config(self.Class_Novel, self.Class_Config)  # 初始化保存配置
        return True

    def _download(self):
        if self.Class_Novel.down_title_list:     # 当有下载章节时
            index = self.Class_Novel.all_title_list.index(self.Class_Novel.down_title_list[0]) - 1
            for title, url in zip(self.Class_Novel.down_title_list, self.Class_Novel.down_url_list):
                index += 1
                if not self.Class_Novel.download(title, url, index, self.download_url): return False
                if self.Class_Config.Save_method: pass
                self.Class_Save.save(title)  # 保存
                self.down_progress.update(1)
            return True
        else:
            return False

    def download_novel(self):
        # 获取被中断的链接
        unprocess = []
        if self.Class_Config.User_config.get('Unprocess',[]) is not None:
            unprocess = set(self.Class_Config.User_config['Unprocess'])
            unprocess.add(self.download_url)  # 防重复的添加
            unprocess = list(unprocess)  # 符合格式的保存
            self.Class_Config.User_config['Unprocess'] = unprocess
            self.Class_Config.save_config(1)
        with tqdm(total=len(self.Class_Novel.down_title_list),
                  desc=self.Class_Novel.novel['info']['name']) as self.down_progress:
            try:
                self._download()
                # 多线程启动self._download() 暂未实现
                for thread_id in range(self.Class_Config.Threads_num):
                    pass
            except KeyboardInterrupt:
                print("已退出..")
        if self.download_url in unprocess:
            unprocess.remove(self.download_url)
            self.Class_Config.User_config['Unprocess'] = unprocess
            self.Class_Config.save_config(1)

    def func(self):

        while True:

            # 重新加载
            self.__init__(self.logger)
            # 中断重新下载
            unprocess = self.Class_Config.User_config['Unprocess']
            if unprocess:
                print("发现未下载完成的链接")
                for index in range(len(unprocess)):
                    print(f"{index+1}.{unprocess[index]}")
                choice = input("请选择或退出(n)")
                if re.match(r"^\d+$",choice.strip()):
                    self.Class_Config.Novel_update = True  # 标记为更新
                    self.load_down_args(unprocess[int(choice) - 1])  # 配置
                    self.download_novel()  # 下载
                else:
                    unprocess = []
                    self.Class_Config.User_config['Unprocess'] = unprocess
                    self.Class_Config.save_config(1)

            current_version = self.Class_Config.User_config['Version']  # 当前用户配置文件
            # 用户配置文件更新
            if current_version != LASTEST_USERCONFIG_VERSION:
                temp = Check.update(current_version, copy.deepcopy(self.Class_Config.User_config))
                if temp:
                    self.Class_Config.User_config = temp
                    self.Class_Config.save_config(1)
            # 备份
            backup_config = self.Class_Config.User_config.get('Backup',{})
            if backup_config.get("Auto",False):
                backup_dict = self.Class_Config.User_manage
                auto_save_method = backup_config.get('Auto_save_method', 'T:86400')
                if auto_save_method.startswith('T:'):
                    gap_time = int(auto_save_method[2:]) if re.match(r"\d+", auto_save_method[2:]) else 86400
                    last_backup_time = backup_config.get("Last_time", 0)
                    now_time = time.time()
                    if now_time - last_backup_time > gap_time:
                        backup(backup_config, backup_dict,auto=True)
                        now_time = time.time()
                        self.Class_Config.User_config["Backup"]["Last_time"] = now_time
                        self.Class_Config.save_config(1)

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
                            """将打开urls.txt,请在文件中输入小说链接，一行一个。输入完成后请保存并关闭文件，然后按 Enter 键继续...""")
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
                        novel_range_ = input('请输入章节范围(如1-3,5,7-9):')
                        self.range = novel_range_
                        self.download_url = self.load_down_args(self.download_url)
                        self.download_novel()
                        """
建议直接通过JSON文件修改配置，这样更快更灵活.（若精通）
"""
                    case "5":
                        choice = input(
                            """
1.账户操作：
2.分组内操作：
3.默认参数修改：
""")
                        match choice:
                            case '1':
                                users = list(self.Class_Config.User_manage['USERS'].keys())
                                print()
                                for user_idx in range(1, len(users) + 1):
                                    print(f"{Fore.BLUE}{user_idx}.{users[user_idx - 1]}")
                                print(f"\n当前账户:{Fore.LIGHTBLUE_EX}{self.Class_Config.USER}")
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
                                                if template_userconfig is None:
                                                    print("无法创建")
                                                else:
                                                    if self.Class_Config.set_new_user(user_input, template_userconfig):
                                                        print(f"账户已创建成功({self.Class_Config.USER})")
                                                break

                                    case "3":
                                        option = input("请选择需删除的账户(数字):").strip()
                                        if not option or 'r' in option.lower():
                                            print("已退出..")
                                        if re.match(r"\d+", option.strip()):
                                            option = int(option)
                                            del_user = self.Class_Config.User_manage["USERS"].pop(option - 1)
                                            if del_user == self.Class_Config.USER:  # 当删除的是当前账户
                                                self.Class_Config.User_manage["USER"] = users[0]
                                            self.Class_Config.save_config(2)
                                            self.Class_Config.load()
                                            print(f"账户 {del_user} 已删除成功({self.Class_Config.USER})")

                            case '2':
                                groups = list(self.Class_Config.mems.keys())
                                # 输出所有Group
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
                                            # 符合选择规范
                                            if re.match(r"\d+", option.strip()):
                                                option = int(option)
                                                self.Class_Config.User_config['Group'] = groups[option - 1]
                                                self.Class_Config.save_config(1)  # 保存为UserConfig.json
                                                self.Class_Config.load()  # 重新加载
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
                                                self.Class_Config.mems[group_input] = {}  # 新建一个group
                                                self.Class_Config.save_config(0)  # 保存mems.json
                                                self.Class_Config.save_config(1)  # 保存UserConfig.json
                                                self.Class_Config.load()  # 重新加载
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
                                            # 如果删除的是当前的GROUP
                                            if del_group == self.Class_Config.GROUP:
                                                self.Class_Config.User_config['Group'] = groups[0]
                                            self.Class_Config.save_config(0)  # 保存mems.json
                                            self.Class_Config.save_config(1)  # 保存UserConfig.json
                                            self.Class_Config.load()  # 重新加载
                                            print(f"分组 {del_group} 已删除成功({self.Class_Config.GROUP})")
                                        else:
                                            print("请正确输入")
                                            continue

                            case '3':
                                option = input(
                                    '''1.获取模式
2.Chrome设置
3.API设置
4.Requests设置
5.保存方式设置
'''
                                )
                                temp = setting(option, self.Class_Config.User_config)
                                if temp:
                                    self.Class_Config.User_config = temp
                                    self.Class_Config.save_config(1)  # 保存
                    case "6":
                        backup_config = self.Class_Config.User_config.get("Backup", {})
                        backup_item = self.Class_Config.User_manage
                        backup_path = backup(backup_config, backup_item)
                        if backup_path:
                            print(f"保存成功，已保存在 {backup_path}")

            except ValueError as error_e:
                if str(error_e).startswith("NovelDownloader:"):
                    continue
                else:
                    raise
            except KeyboardInterrupt:
                code = input("是否退出？y/n")
                if 'y' in code.lower() or 'Y' in code.lower():
                    sys.exit(0)
                else:
                    continue
        return True

    def __init__(self, logger_):

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

if __name__ == "__main__":
    args = sys.argv
    if len(args) > 2:
        downloader = NovelDownloader(logger)
        download_url = None
        novel_update = True
        novel_range = None
        for arg in args[1:]:
            if arg.startswith("--url="):
                download_url = arg[len("--url="):].split("?")[0]
            elif arg.startswith("--update="):
                novel_update = arg[len("--update="):].split("?")[0]
                if novel_update.lower().startswith('f'):
                    novel_update = False
            elif arg.startswith("--range="):
                novel_range = arg[len("--range="):].split("?")[0]
                downloader.range = novel_range
        if download_url is None:
            print("请指定url")
            exit(1)
        else:
            downloader.Class_Config.Novel_update = novel_update
            downloader.range = novel_range
            downloader.load_down_args(download_url)
            downloader.download_novel()
            exit(0)

    else:
        print(f"""
作者：Canyang2008
项目地址：https://github.com/canyang2008/NovelDownloader
检查配置中……{Fore.YELLOW}\n\n""")

        Check.main(template_userconfig)
        # sys.excepthook = global_exception_handler  # 设置全局异常处理器
        downloader = NovelDownloader(logger)
        downloader.func()  # 功能
