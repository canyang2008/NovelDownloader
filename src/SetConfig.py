import copy
import json
import os


class SetConfig:
    """配置类"""

    def __init__(self):
        self.Threads_num = 1
        self.Api_option = None
        self.Api_key = None
        self.Play_completion_sound = None
        self.Port = None
        self.USER = "Default"
        self.GROUP = "Default"
        self.Novel_update = False
        self.Max_retry = 3
        self.Timeout = 10
        self.Interval = 2
        self.Group = None
        self.Save_method = None
        self.Delay = [1, 3]
        self.url = ""
        self.mems = None
        self.Base_dir = None
        self.User_data_dir = None
        self.User_data_dir = None
        self.Get_mode = 0
        self.User_config = None
        self.User_config_path = None
        self.User_manage = None
        self.load()
        self.Headless = False
        self.Browser_path = None

    def load(self):
        # 读取所有用户管理配置
        with open("data/Local/manage.json", "r", encoding="utf-8") as f:
            self.User_manage = json.load(f)

        # 读取当前用户所配置的文件目录/路径
        self.USER = self.User_manage.get("USER", "Default")
        default_user_config = {
            "User_config_path": f"data/Local/{self.USER}/UserConfig.json",
            "User_data_dir": f"data/Local/{self.USER}/User Data",
            "Base_dir": f"data/Local/{self.USER}/json"}
        user_config_paths = self.User_manage["USERS"].get(self.USER, default_user_config)
        self.User_config_path = user_config_paths.get("User_config_path", default_user_config["User_config_path"])
        self.User_data_dir = user_config_paths.get("User_data_dir", default_user_config["User_data_dir"])
        self.Base_dir = user_config_paths.get("Base_dir", default_user_config["Base_dir"])

        # 读取用户配置(UserConfig.json)
        with open(self.User_config_path, "r", encoding="utf-8") as f:
            self.User_config = json.load(f)
        self.GROUP = self.User_config.get("Group", "Default")
        self.Group = self.GROUP
        self.Get_mode = self.User_config.get("Get_mode", 0)
        self.Save_method = self.User_config.get("Save_method", {})
        self.Threads_num = self.User_config.get("Threads_num", 1)
        if self.Get_mode == 0:
            self.Port = self.User_config["Browser"].get("Port", 9444)
            self.Max_retry = self.User_config["Browser"].get("Max_retry", 3)
            self.Timeout = self.User_config["Browser"].get("Timeout", 10)
            self.Interval = self.User_config["Browser"].get("Interval", 2)
            self.Delay = self.User_config["Browser"].get("Delay", [1, 3])

        self.Play_completion_sound = self.User_config.get("Play_completion_sound", False)

        # 读取mems.json
        with open(os.path.join(self.Base_dir, 'mems.json'), "r", encoding="utf-8") as f:
            self.mems = json.load(f)

    def set_new_user(self, user_name:str, template:dict, template_mems) -> bool:
        new_userconfig = copy.deepcopy(template)
        new_userconfig["User_name"] = user_name
        new_userconfig['Browser']["port"] = 9444 + len(self.User_manage["USERS"].keys())    # 端口号不能与其他用户的相同
        os.makedirs(f"data/Local/{user_name}/json", exist_ok=True)
        with open(f"data/Local/{user_name}/UserConfig.json", "w", encoding="utf-8") as f:
            json.dump(new_userconfig, f, ensure_ascii=False, indent=4)
        with open(f"data/Local/{user_name}/json/mems.json", "w", encoding="utf-8") as f:
            json.dump(template_mems, f, ensure_ascii=False, indent=4)
        self.User_manage["USERS"][user_name] = {
            "User_config_path": f"data/Local/{user_name}/UserConfig.json",
            "User_data_dir": f"data/Local/{user_name}/User Data",
            "Basfe_dir": f"data/Local/{user_name}/json"
        }
        self.User_config['USER'] = user_name
        self.save_config(2)     # 保存manage.json
        self.load()
        return True

    def set_config(self, url):
        if self.Novel_update:
            for group in self.mems.keys():
                if group == "Version": continue
                if url in self.mems[group].keys():  # 如果url存在于成员内
                    self.Novel_update = True
                    self.Group = group
                    file_name = self.mems[self.Group][
                                    url] + '.json'  # 需要读取的文件全名
                    json_path = os.path.join(self.Base_dir,file_name)  # 路径
                    if not os.path.exists(json_path):
                        print('json文件被移动或不存在')
                        self.Novel_update = False
                        self.set_config(url)
                    else:
                        with open(os.path.join("data", "Local", self.USER, "json", file_name), "r", encoding="utf-8") as f:
                            novel_config = json.load(f)['config']
                        self.Get_mode = novel_config.get("Get_mode", 0)
                        self.Max_retry = novel_config.get("Max_retry", 3)
                        self.Timeout = novel_config.get("Timeout", 10)
                        self.Interval = novel_config.get("Interval", 2)
                        self.Delay = novel_config.get("Delay", [1, 3])
                        self.Save_method = copy.deepcopy(novel_config["Save_method"])
                        return True


        self.Group = self.GROUP
        if self.Get_mode == 1:
            if 'fanqienovel.com' in url:
                website = 'Fanqie'
            elif 'qidian.com' in url:
                website = 'Qidian'
            else:
                print('不支持该网站，请检查链接')
                raise ValueError(f"NovelDownloader:The website corresponding to this url does not support\nUrl: {url}")
            self.Api_option = self.User_config["Api"][website]["Option"]
            api_config = self.User_config["Api"][website][self.Api_option]
            self.Max_retry = api_config.get("Max_retry", 3)
            self.Timeout = api_config.get("Timeout", 10)
            self.Interval = api_config.get("Interval", 2)
            self.Delay = api_config.get("Delay", [1, 3])
            if self.Api_option == "oiapi":
                self.Api_key = api_config.get("Key")
        else:
            self.Port = self.User_config["Browser"].get("Port", 9445)
            self.Max_retry = self.User_config['Browser'].get("Max_retry", 3)
            self.Timeout = self.User_config['Browser'].get("Timeout", 10)
            self.Interval = self.User_config['Browser'].get("Interval", 2)
            self.Delay = self.User_config['Browser'].get("Delay", [1, 3])
        self.Novel_update = False
        return None

    def save_config(self, option=0):

        match option:
            case 0:  # 保存mems.json
                mems_format = json.dumps(self.mems, ensure_ascii=False, indent=4)
                with open(os.path.join(self.Base_dir, 'mems.json'), "w", encoding="utf-8") as f:
                    f.write(mems_format)

            case 1:  # 保存UserConfig.json
                # 检查文件是否完整

                user_config_format = json.dumps(self.User_config, ensure_ascii=False, indent=4)
                with open(self.User_config_path, "w", encoding="utf-8") as f:
                    f.write(user_config_format)

            case 2:  # 保存manage.json
                manage_format = json.dumps(self.User_manage, ensure_ascii=False, indent=4)
                with open("data/Local/manage.json", "w", encoding="utf-8") as f:
                    f.write(manage_format)

        return True
