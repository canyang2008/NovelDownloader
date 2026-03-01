import base64
import json
import os
from novel_downloader import SaveMethodConfig, DownloadMode
from novel_downloader.models.group import Group
from novel_downloader.models.novel import Novel, Chapter,json_to_img


class NovelStorage:
    """小说存储管理"""

    def __init__(self, config):
        self.config = config
        self._last_backup_time = {}
    @staticmethod
    def read_novel_data(path: str) -> list:
        """
        读取新版 JSON Lines 格式的小说数据文件。
        文件包含三种记录类型（顺序可能任意）：
        - 小说基本信息（包含 'cover_image_data'）
        - 组配置（包含 'group_name' 和 'mode'）
        - 章节数据（包含 'images'）
        返回按最后更新时间排序的小说列表。
        """
        novel_list = []
        current_novel = None

        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    # 可添加日志警告，此处直接忽略损坏行
                    continue

                # 1. 小说基本信息
                if 'cover_image_data' in data:
                    # 构造 Novel 对象（注意字段名与类属性一致）
                    novel = Novel(
                        url=data.get('url'),
                        name=data.get('name'),
                        author=data.get('author'),
                        author_description=data.get('author_description'),
                        tags=data.get('tags'),                # 预期为列表
                        description=data.get('description'),
                        count=data.get('count'),
                        last_update_chapter=data.get('last_update_chapter'),
                        last_update_time=data.get('last_update_time'),
                        rating=data.get('rating'),
                        cover_image_data=base64.b64decode(data['cover_image_data']),
                    )
                    current_novel = novel
                    novel_list.append(novel)

                # 2. 组配置（必须已存在当前小说）
                elif 'group_name' in data and 'mode' in data and current_novel is not None:
                    # 处理特殊字段
                    mode = DownloadMode(data['mode']) if data.get('mode') is not None else None
                    delay = tuple(data['delay']) if data.get('delay') is not None else None
                    save_method = None
                    if data.get('save_method'):
                        save_method = SaveMethodConfig(**data['save_method'])

                    group = Group(
                        group_name=data.get('group_name'),
                        novel_name=data.get('novel_name'),
                        file_path=data.get('file_path'),
                        url=data.get('url'),
                        mode=mode,
                        thread_count=data.get('thread_count'),
                        timeout=data.get('timeout'),
                        delay=delay,
                        max_retry=data.get('max_retry'),
                        interval=data.get('interval'),
                        user_data_dir=data.get('user_data_dir'),
                        port=data.get('port'),
                        headless=data.get('headless'),
                        api_address=data.get('api_address'),
                        api_key=data.get('api_key'),
                        endpoint=data.get('endpoint'),
                        params=data.get('params'),
                        cookies=data.get('cookies'),
                        headers=data.get('headers'),
                        proxies=data.get('proxies'),
                        save_method=save_method
                    )
                    current_novel.group = group

                # 3. 章节数据（必须已存在当前小说）
                elif 'images' in data and current_novel is not None:
                    chapter = Chapter(
                        title=data.get('title'),
                        url=data.get('url'),
                        order=data.get('order'),
                        volume=data.get('volume'),
                        content=data.get('content'),
                        timestamp=data.get('timestamp'),
                        count=data.get('count'),
                        is_complete=data.get('is_complete'),
                    )
                    chapter.images = json_to_img(data['images'])
                    current_novel.update(chapter)

                # 4. 未知类型：可记录警告后忽略
                else:
                    # 例如：日志记录未知行，但当前处理中直接跳过
                    pass

        # 按最后更新时间排序（从新到旧）
        novel_list.sort(key=lambda x: x.last_update_time, reverse=True)
        return novel_list
    @staticmethod
    def mix_latest_novel(novel_list:list[Novel]) -> Novel:        # 读取所有小说版本，混合成所有最新完整的小说
        novel_list.reverse()
        latest_novel = novel_list[0]
        for novel in novel_list[1:]:
            for chapter in novel.chapters:
                latest_novel += chapter
        return latest_novel

    def backup_novel(self, backup_config) -> str:
        """备份配置"""
        pass

    def cleanup_old_backups(self, backup_path: str):
        """清理旧备份"""
        pass