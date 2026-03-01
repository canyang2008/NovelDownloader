import os
import re
import time
from typing import Any
from .base import Output
from novel_downloader.models.save import TxtSaveConfig


class TXTOutput(Output):
    """TXT输出格式，支持多种切割策略和乱序章节处理"""

    def __init__(self, save_config: TxtSaveConfig):
        super().__init__(save_config)
        self.order_chapter_dict: dict[int, Any] = {}  # order -> Chapter对象

    def save(self, chapters, **kwargs):
        """保存一批章节（可能乱序），更新缓存并重新输出"""
        if self.save_config.enable is not None and not self.save_config.enable:
            return None

        # 更新缓存
        for chapter in chapters:
            if chapter is not None:
                self.order_chapter_dict[chapter.order] = chapter

        # 根据配置模式执行写入
        if self.save_config.chapters_per_file and self.save_config.chapters_per_file>0:
            self._write_multi_files_by_chapter_count()
        elif self.save_config.file_size and self.save_config.file_size>0:
            self._write_multi_files_by_size()
        else:
            self._write_single_file()

        return None

    def _write_single_file(self):
        """单文件模式：写入或更新主文件（保持文件打开）"""
        output_dir = self.save_config.output_dir
        os.makedirs(output_dir, exist_ok=True)
        file_path = os.path.join(output_dir, self.save_config.file_name + self.save_config.extension)

        # 打开并写入小说信息
        with open(file_path, 'w', encoding=self.save_config.encoding) as f:
            info_text = self._generate_info_text()
            f.write(info_text)
            sorted_orders = sorted(self.order_chapter_dict.keys())
            for order in sorted_orders:
                chapter = self.order_chapter_dict[order]
                chapter_text = self._format_chapter(chapter)
                f.write(chapter_text)

    def _write_multi_files_by_chapter_count(self):
        per_file = self.save_config.chapters_per_file
        base_dir = os.path.join(self.save_config.output_dir, f"chapters_per_file_{per_file}")
        os.makedirs(base_dir, exist_ok=True)

        # 写入独立的小说信息文件
        info_path = os.path.join(base_dir, "小说信息.txt")
        with open(info_path, 'w', encoding=self.save_config.encoding) as f:
            f.write(self._generate_info_text())

        # 排序章节
        sorted_orders = sorted(self.order_chapter_dict.keys())
        all_chapters = [self.order_chapter_dict[order] for order in sorted_orders]

        # 分组
        groups = [all_chapters[i:i + per_file] for i in range(0, len(all_chapters), per_file)]

        # 写入分组文件
        for idx, group in enumerate(groups, start=1):
            file_name = f"{idx}{self.save_config.extension}"
            file_path = os.path.join(base_dir, file_name)
            with open(file_path, 'w', encoding=self.save_config.encoding) as f:
                for chapter in group:
                    f.write(self._format_chapter(chapter))

    def _write_multi_files_by_size(self):
        max_mb = self.save_config.file_size
        max_bytes = max_mb * 1024 * 1024
        base_dir = os.path.join(self.save_config.output_dir, f"file_size_{max_mb}MB")
        os.makedirs(base_dir, exist_ok=True)

        # 写入独立的小说信息文件
        info_path = os.path.join(base_dir, "小说信息.txt")
        with open(info_path, 'w', encoding=self.save_config.encoding) as f:
            f.write(self._generate_info_text())

        # 排序章节
        sorted_orders = sorted(self.order_chapter_dict.keys())
        all_chapters = [self.order_chapter_dict[order] for order in sorted_orders]

        # 按大小分组
        groups = []
        current_group = []
        current_size = 0

        for chapter in all_chapters:
            chap_text = self._format_chapter(chapter)
            chap_bytes = len(chap_text.encode(self.save_config.encoding))

            # 如果当前组为空，直接加入（即使单章超过大小也强制放入）
            if not current_group:
                current_group.append(chapter)
                current_size = chap_bytes
            else:
                if current_size + chap_bytes > max_bytes:
                    groups.append(current_group)
                    current_group = [chapter]
                    current_size = chap_bytes
                else:
                    current_group.append(chapter)
                    current_size += chap_bytes

        if current_group:
            groups.append(current_group)

        # 写入分组文件
        for idx, group in enumerate(groups, start=1):
            file_name = f"{idx}{self.save_config.extension}"
            file_path = os.path.join(base_dir, file_name)
            with open(file_path, 'w', encoding=self.save_config.encoding) as f:
                for chapter in group:
                    f.write(self._format_chapter(chapter))

    # ---------- 辅助方法 ----------

    def _generate_info_text(self) -> str:
        """生成小说信息文本"""
        novel = self.novel
        return (
            f"小说名：{novel.name}\n作者：{novel.author}\n"
            f"简介：{novel.description}\n标签：{' '.join(novel.tags)}\n"
            f"字数：{novel.count}\n"
            f"最后更新：{novel.last_update_chapter} "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(novel.last_update_time))}\n"
            f"链接：{novel.url}\n\n"
        )
    @staticmethod
    def _format_chapter(chapter) -> str:
        """将单个Chapter对象格式化为文本"""
        content = '\t' + chapter.content.replace("\n", "\n\t")
        content = re.sub(r'<&!img\?group_id=\d+/!&>', '', content)  # 去除图片占位符
        return (
            f"{chapter.title}\n    "
            f"更新字数：{chapter.count}    "
            f"更新时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(chapter.timestamp))}\n\n"
            f"{content}\n\n"
        )
    def close(self):pass