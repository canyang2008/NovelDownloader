from abc import ABC, abstractmethod
from typing import Any

from novel_downloader.models.save import BaseSaveConfig


class Output(ABC):
    """输出格式基类"""

    @abstractmethod
    def __init__(self, save_config):
        self.save_config = save_config
        self.novel: Any | None = None   # Novel对象
        pass

    @abstractmethod
    def save(self, chapters, **kwargs):
        """保存小说到指定格式"""
        pass

    @abstractmethod
    def close(self):
        pass


import json
import os
import base64
from novel_downloader.models.novel import img_to_json
from dataclasses import asdict


class BASEOutput(Output):
    """根数据输出"""

    def __init__(self, save_config: BaseSaveConfig):
        self.base_dir = None
        self.file_path = None
        self.img_dir = None
        super().__init__(save_config)
        self.__file = None

    def save(self, chapters, **kwargs):
        if self.save_config.enable is not None and not self.save_config.enable:
            return None
        if self.__file is None:
            self.file_path = os.path.join(self.save_config.output_dir, self.novel.name + ".json")
            if os.path.exists(self.file_path):
                write_next = True
            else:
                write_next = False
            self.__file = open(self.file_path, 'a', encoding="utf-8")
            if write_next:
                self.__file.write("\n")
            page_json_data = asdict(self.novel) # 初始化时使用这个占用的内存不多
            page_json_data["cover_image_data"] = base64.b64encode(self.novel.cover_image_data).decode()
            page_json_data.pop("chapters")
            page_json_data.pop("group")
            page_json_data.pop("_Novel__chapter_by_order")
            page_json_data.pop("_Novel__chapter_by_url")
            self.__file.write(json.dumps(page_json_data, ensure_ascii=False, separators=(',', ':')))
            self.__file.write("\n")
            config_json_data = asdict(self.novel.group)
            config_json_data['mode'] = config_json_data['mode'].value
            self.__file.write(json.dumps(config_json_data, ensure_ascii=False, separators=(',', ':')))
            self.__file.write("\n")

        for chapter in chapters:
            if not chapter:continue
            img_datas = img_to_json(chapter.images)
            json_data = asdict(chapter)
            json_data["images"] = img_datas

            self.__file.write(json.dumps(json_data, ensure_ascii=False, separators=(',', ':')))
            self.__file.write("\n")
            pass
        return None

    def close(self):
        if self.__file:
            self.__file.close()
