from DrissionPage import Chromium, ChromiumOptions
from colorama import Fore, init

init(autoreset=True)  # 初始化colorama，自动重置颜色


class RunDriver:

    def __init__(self, logger_):

        self.logger = logger_
        self.co = None
        self.options = None
        self.tab = None
        self.driver = None

    def config(self, user_data_dir, port, headless):
        self.co = ChromiumOptions()
        self.co = self.co.set_user_data_path(user_data_dir)
        self.co = self.co.set_local_port(port)
        self.co = self.co.headless(headless)
        pass
    def run(self):
        try:
            self.driver = Chromium(addr_or_opts=self.co)
            if self.driver.states.is_existed:
                self.tab = self.driver.new_tab()
                self.tab.set.window.mini()
            else:
                self.tab = self.driver.get_tab()
        except Exception as e:
            print(f"{Fore.LIGHTRED_EX}Chromium无法启动，信息:{e}")
            exit(1)
        return self.tab
