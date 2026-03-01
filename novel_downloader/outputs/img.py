import os

from novel_downloader.outputs.base import Output
from novel_downloader.models.save import ImgSaveConfig
from . import sanitize_name
class IMGOutput(Output):
    def __init__(self,save_config:ImgSaveConfig):
        self.save_config = None
        self.cover_saved = False
        super().__init__(save_config)
    def save(self, chapters, **kwargs):
        if self.save_config.enable is not None and not self.save_config.enable:
            return None
        if not self.cover_saved:
            os.makedirs(os.path.join(self.save_config.output_dir, "封面图片"),exist_ok=True)
            with open(os.path.join(self.save_config.output_dir, "封面图片",f"{self.novel.name}.png"), "wb") as f:
                f.write(self.novel.cover_image_data)
            self.cover_saved = True
        for chapter in chapters:
            if chapter.images:
                sanitize_chapter_title = sanitize_name(chapter.title)
                os.makedirs(os.path.join(self.save_config.output_dir, sanitize_chapter_title), exist_ok=True)
                for item in chapter.images:
                    img_file_name = os.path.join(self.save_config.output_dir, sanitize_chapter_title, sanitize_name(item[0]))
                    with open(img_file_name, "wb") as f:
                        f.write(item[1])

    def close(self):pass