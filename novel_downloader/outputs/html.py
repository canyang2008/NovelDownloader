import base64
import os
import re
import time

from novel_downloader.models.novel import img_to_json
from novel_downloader.models.save import HtmlSaveConfig
from novel_downloader.outputs.base import Output

class HTMLOutput(Output):

    def __init__(self, save_config:HtmlSaveConfig):
        super().__init__(save_config)
        self.json_data = None

    def save(self, chapters, **kwargs):
        return None
        if self.__file is None:
            file_path = os.path.join(self.save_config.output_dir, self.save_config.file_name+self.save_config.extension)
            os.makedirs(self.save_config.output_dir, exist_ok=True)
            self.__file = open(file_path, "w", encoding='utf-8')
            self.json_data = {
                "info":{
                    "name": self.novel.name,
                    "author": self.novel.author,
                    "author_desc": self.novel.author_description,
                    "label": " ".join(self.novel.tags),
                    "count_word": str(self.novel.count) + "字",
                    "last_update": f"最近更新：{self.novel.last_update_chapter}  {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.novel.last_update_time))}",
                    "abstract": self.novel.description,
                    "book_cover_data": "data:image/png;base64," + base64.b64encode(self.novel.cover_image_data).decode(),
                    "url": self.novel.url,
                },
                "chapters":{},
            }
        for chapter in chapters:
            if chapter is None:
                continue
            self.json_data["chapters"][chapter.title] = {
                "url": chapter.url,
                "update":f"更新时间：{time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(chapter.timestamp))}",
                "count_word":f"本章字数：{chapter.count}字",
                "content":re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter.content),
                "integrity":chapter.is_complete,
                "img_item":img_to_json(chapter.images),
            }
        pass

    def close(self):
        pass


