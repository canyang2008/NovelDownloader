from DrissionPage import Chromium, ChromiumOptions
from colorama import Fore, init

init(autoreset=True)  # 初始化colorama，自动重置颜色


class RunDriver:

    def __init__(self, logger_):

        self.logger = logger_
        self.co = None
        self.options = None
        self.driver = None

    def config(self, Class_Config, headless=False):
        self.co = ChromiumOptions().set_user_data_path(Class_Config.User_data_dir).headless(headless)

    def run(self):
        try:
            self.driver = Chromium(addr_or_opts=self.co)
            if self.driver.states.is_existed:
                self.driver = self.driver.new_tab()
                self.driver.set.window.mini()
            else:
                self.driver = self.driver.get_tab()
        except Exception as e:
            self.driver.quit()
            print(f"{Fore.LIGHTRED_EX}Chromium无法启动，信息:{e}")
            exit(1)
        return self.driver
