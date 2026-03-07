import threading
from dataclasses import dataclass, field
import base64
from typing import Iterable
from novel_downloader.models.group import Group

threadLock = threading.Lock()
def json_to_img(json_data):
    if json_data:
        img_datas = []
        for img in json_data:
            img_desc = img[0]
            img_data = base64.b64decode(img[1])
            img_datas.append((img_desc,img_data))
        return img_datas
    else:return []


def img_to_json(images):
    if images:
        img_datas = []
        for img in images:
            img_desc = img[0]
            img_data = base64.b64encode(img[1]).decode()
            img_datas.append((img_desc,img_data))
        return img_datas
    else:
        return []

@dataclass
class Chapter:
    """章节数据"""
    title: str
    order: int
    url: str|None = None
    volume:str = ""
    content: str = ""
    timestamp: float = 0
    count:int = 0
    is_complete: bool = False
    images: list[tuple[str,bytes]] = field(default_factory=list)
    def __hash__(self) -> int:
        return hash((self.title,self.url))

    def __eq__(self,chapter):
        if not isinstance(chapter, Chapter):
            return NotImplemented
        return self.title == chapter.title and \
            self.url == chapter.url and \
            self.order == chapter.order and \
            self.volume == chapter.volume and \
            self.content == chapter.content and \
            self.timestamp == chapter.timestamp and \
            self.is_complete == chapter.is_complete and \
            self.images == chapter.images

    def __repr__(self):
        return f"Chapter({self.order}, '{self.title}')"


@dataclass
class Novel:
    """小说数据"""
    url: str
    name: str
    total: int = 0
    author: str | None = None
    author_description: str | None = None
    tags: list[str] = field(default_factory=list)
    description: str | None = None
    count: int = 0
    last_update_chapter: str | None = None
    last_update_time: float | None = None
    rating: float | None = None
    cover_image_data: bytes = b''
    chapters: list[Chapter] = field(default_factory=list)
    group:Group | None = None

    # 索引字段
    __chapter_by_url: dict[str, Chapter] = field(default_factory=dict, init=False)
    __chapter_by_order: dict[int, Chapter] = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.__thread_lock = threading.Lock()

    def __hash__(self) -> int:
        return hash((
            self.url,
            self.name,
            self.author,
            self.author_description,
            self.tags,
            self.description,
            self.count,
            self.last_update_chapter,
            self.last_update_time,
            self.rating,
            self.cover_image_data,
            self.chapters
        ))
    def update(self, chapters: Iterable[Chapter] | Chapter):
        if not isinstance(chapters, Iterable):
            chapters = [chapters]
        for chapter in chapters:
            if chapter:
                self.__thread_lock.acquire()
                if chapter.url:
                    self.__chapter_by_url[chapter.url] = chapter
                if chapter.order!=0:
                    self.__chapter_by_order[chapter.order] = chapter
                self.chapters = list(self.__chapter_by_order.values())
                self.__thread_lock.release()
        return self

    def __getitem__(self, index):
        if isinstance(index,str) and index.strip().startswith("https://"):
            return self.__chapter_by_url.get(index)
        elif isinstance(index,int):
            return self.__chapter_by_order.get(index)
        return None
    def find_chapter(self,order:int = None, url:str = None, title_key:str = None) ->list[Chapter]|Chapter|None:
        if order:
            return self.__chapter_by_order.get(order)
        if url:
            return self.__chapter_by_url.get(url)
        if title_key:
            probable_chpaters = []
            for chapter in self.chapters:
                if title_key in chapter.title:
                    probable_chpaters.append(chapter)
            return probable_chpaters
        return None