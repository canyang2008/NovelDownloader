import copy
import json
import time
from pathlib import Path


class SetConfig:
    """配置类"""

    def __init__(self):

        """初始化配置"""
        self.config_url = None
        with open('data/Record/UrlConfig.json', 'r', encoding='utf-8') as f:
            self.url_config = json.load(f)
        with open('data/Record/SettingConfig.json', 'r', encoding='utf-8') as f:
            self.setting_config = json.load(f)
        self.setting_config['Program_location'] = str(Path(__file__).parent.resolve())  # 程序位置
        self.Main_user = self.setting_config.get('User')
        self.User = self.Main_user
        self.Group = self.setting_config.get('Group')
        self.Main_group = self.Group
        default_config = self.setting_config['Default']
        # 如果下载链接不在任何组的配置中，使用默认配置
        self.User_data_dir = default_config.get('User_data_dir')
        self.Wait_time = default_config.get('Wait_time')
        self.Save_method = default_config.get('Save_method')
        self.Save_method = copy.deepcopy(self.Save_method)
        self.config_update = False

    def save_config(self):
        """保存配置"""
        url_config_format = json.dumps(self.url_config, ensure_ascii=False, indent=4)  # 防止写入中断
        with open('data/Record/UrlConfig.json', 'w', encoding='utf-8') as f:
            f.write(url_config_format)

        setting_config_format = json.dumps(self.setting_config, ensure_ascii=False, indent=4)  # 防止写入中断
        with open('data/Record/SettingConfig.json', 'w', encoding='utf-8') as f:
            f.write(setting_config_format)

        return True

    def set_url_config(self, config_url):
        """设置下载链接的配置"""
        self.config_url = config_url

        for user in self.url_config.keys():
            if user == "Version": continue
            for group in self.url_config[user].keys():
                # 如果下载链接在当前组的配置中
                if config_url in self.url_config[user][group].keys():
                    self.User = user
                    self.Group = group
                    self.User_data_dir = self.url_config[user][group][config_url].get('User_data_dir')
                    self.Wait_time = self.url_config[user][group][config_url].get('Wait_time')
                    self.Save_method = self.url_config[user][group][config_url].get('Save_method')
                    self.config_update = True
                    return

        self.User = self.Main_user
        self.Group = self.Main_group

    def add_url_config(self, name, state):
        """添加或更新con.url_config中的配置"""
        if self.config_update:
            self.url_config[self.User][self.Group][self.config_url]['Name'] = name
            self.url_config[self.User][self.Group][self.config_url]['State'] = state
            self.url_config[self.User][self.Group][self.config_url]['Last_control_timestamp'] = time.time()
            self.url_config[self.User][self.Group][self.config_url]['Last_control_time'] = time.strftime(
                '%Y-%m-%d %H:%M:%S',
                                                                                              time.localtime(
                                                                                                  time.time()))
        else:
            # 创建一个新的记录
            if self.User not in self.url_config.keys(): self.url_config[self.User] = {}  # 创建新的账户
            if self.Group not in self.url_config[self.User].keys(): self.url_config[self.User][self.Group] = {}  # 创建新的组
            self.url_config[self.User][self.Group][self.config_url] = {
                'Name': name,
                'State': state,
                'User_data_dir': self.User_data_dir,
                'Save_method': self.Save_method,
                'Wait_time': self.Wait_time,
                'First_timestamp': time.time(),
                'First_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                'Last_control_timestamp': time.time(),
                'Last_control_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
            }
            self.config_update = True

