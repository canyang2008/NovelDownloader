from abc import ABC, abstractmethod
from typing import Any
class BaseParser(ABC):
    """解析器基类"""
    def __init__(self, **kwargs):
        self.downloader = None
        self.novel = None
        self.batch_size = 1
        self.user_status = -1

    @abstractmethod
    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> str | None:
        """搜索小说信息
        Return:
        [{
            "name": ,
            "author": ,
            "tags": ,
            "word_count": ,
            "read_count": ,
            "chapters_count": ,
            "description": ,
            "latest_chapter": ,
            "update_time": ,
            "cover_url": ,
            "book_url": ,
            "need_unlock": ,
            "platform": ,
            ...
        }]"""
        pass


    @abstractmethod
    def parse_novel_info(self, content, **kwargs) -> Any | None:
        """解析小说信息"""
        pass

    @abstractmethod
    def parse_chapter_content(self, content, orders, **kwargs) -> tuple[Any | None,...]:
        """解析章节内容"""
        pass
