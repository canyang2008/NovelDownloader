from DrissionPage import Chromium, ChromiumOptions
from colorama import Fore, init

init(autoreset=True)  # 初始化colorama，自动重置颜色


class RunDriver:

    def __init__(self, logger_):

        self.logger = logger_
        self.co = None
        self.options = None
        self.tab = None

    def config(self, Class_Config, headless=False):
        self.co = ChromiumOptions().set_user_data_path(Class_Config.User_data_dir).headless(headless)

    def run(self):
        try:
            driver = Chromium(addr_or_opts=self.co)
            if driver.states.is_existed:
                self.tab = driver.new_tab()
                self.tab.set.window.mini()
            else:
                self.tab = driver.get_tab()
        except Exception as e:
            print(f"{Fore.LIGHTRED_EX}Chromium无法启动，信息:{e}")
            exit(1)
        return self.tab
