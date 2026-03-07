from enum import Enum


class DownloadMode(Enum):
    """下载模式枚举"""
    BROWSER = 0
    API = 1
    REQUESTS = 2

    def __str__(self):
        return str(self.value)
    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        return super().__eq__(other)

class Website(Enum):
    FANQIE = "fanqie"
    QIDIAN = "qidian"
    BIQUGE = "biquge"
    KUAISHU = "kuaishu"
    OTHER = "other"

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    def __hash__(self):
        return hash(self.value)