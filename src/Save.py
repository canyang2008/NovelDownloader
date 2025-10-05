import base64
import copy
import json
import os
import re
import time
from pathlib import Path


class Save:
    def __init__(self, logger_):

        self.novel_name = None
        self.logger = logger_
        self.saved_novel = {}
        self.size_texts = []
        self.full_save = None
        self.save_config = None
        self.Class_Novel = None
        self.Class_Config = None

    def config(self, class_novel, class_config):
        self.Class_Novel = class_novel
        self.Class_Config = class_config

        self.save_config = copy.deepcopy(self.Class_Config.Save_method)     # 以防影响到UserConfig.json的Save_method

        self.novel_name = self.Class_Novel.novel['info']['name']
        novel_info = self.Class_Novel.novel['info']
        novel_abstract = novel_info['abstract'].replace('\n', '\n\t')
        info_text = (  # 生成小说信息文本
                f"小说名：{self.novel_name}\n作者：{novel_info['author']}\n"
                f"简介：{novel_abstract}\n标签：{novel_info['label']}\n"
                f"字数：{novel_info['count_word']}\n最后更新：{novel_info['last_update']}\n"
                f"链接：{novel_info['url']}\n\n"
            )

        self.saved_novel['小说信息'] = {
            "img": {
                'saved': False,
                'item': {
                    "封面图片":self.Class_Novel.novel['info']["book_cover_data"]
                }
            },
            "txt": {
                'saved': False,
                'text': info_text,
                'size': len(info_text.encode('utf-8'))
            },
            "epub": {
                'saved': False
            },
            "html": {
                'saved': False
            }
        }
        def dir_trans(path_parts):  # 特殊路径转化
            if '<User>' in path_parts:
                tp = path_parts.index('<User>')
                path_parts[tp] = self.Class_Config.USER     # 替换为当前USER
            if '<Group>' in path_parts:
                tp = path_parts.index('<Group>')
                path_parts[tp] = self.Class_Config.Group     # 替换为当前GROUP
            if '<Name>' in path_parts:
                tp = path_parts.index('<Name>')              # 替换为当前小说名字
                path_parts[tp] = self.novel_name
            path = path_parts[0] + '\\'.join(path_parts[1:]) if os.path.isabs(
                self.Class_Config.Save_method[file_format]['dir']) else '\\'.join(path_parts)
            return path

        for file_format, config in self.save_config.items():
            # === 配置准备 ===
            # 常规特殊目录转化
            novel_dir_parts = list(Path(self.Class_Config.Save_method[file_format]['dir']).parts)
            config['dir'] = dir_trans(novel_dir_parts)

            # 再次创建gap和max_filesize对应的目录
            gap = self.save_config[file_format].get('gap', -1)
            if gap > 0:
                config['gap_dir'] = os.path.join(config['dir'], f'{file_format} gap={gap}')
                os.makedirs(config['gap_dir'], exist_ok=True)

            max_filesize = self.save_config[file_format].get('max_filesize', -1)
            if max_filesize > 0:
                config['size_dir'] = os.path.join(config['dir'], f'{file_format} size={max_filesize}KB')
                os.makedirs(config['size_dir'], exist_ok=True)

            if file_format == 'json':  # 保存图片路径转化
                image_dir_parts = list(Path(self.Class_Config.Save_method[file_format]['img_dir']).parts)
                config['img_dir'] = dir_trans(image_dir_parts)

                # 处理目录路径
                config['img_dir'] = Path(config.get('img_dir', Path(__file__).parent)).resolve()
                # 确保目录存在
                config['img_dir'].mkdir(parents=True, exist_ok=True)

            # 设置默认文件名
            if config.get('name') == 'name_default':
                config['name'] = f"{self.novel_name}.{file_format}"
            # 确保文件名有正确扩展名
            elif not re.search(f'.{file_format}$', config['name']):
                config['name'] += f'.{file_format}'

            # 处理目录路径
            config['dir'] = Path(config.get('dir', Path(__file__).parent)).resolve()
            # 创建完整文件路径
            config['filepath'] = config['dir'] / config['name']

            # 确保目录存在
            config['dir'].mkdir(parents=True, exist_ok=True)
            # === 配置准备结束 ===

        # 小说配置
        timestamp = time.time()
        self.Class_Config.mems[self.Class_Config.Group][self.Class_Novel.novel['info']['url']] = \
            self.Class_Novel.novel['info']['name']
        novel_config = {
            "Version": "1.1.0",
            "Name": self.Class_Novel.novel['info']['name'],
            "Group": self.Class_Config.Group,
            "Max_retry": self.Class_Config.Max_retry,
            "Timeout": self.Class_Config.Timeout,
            "Interval": self.Class_Config.Interval,
            "Delay": self.Class_Config.Delay,
            "Save_method": self.Class_Config.Save_method,
            "First_time_stamp": timestamp,
            'Last_control_timestamp': timestamp,
        }
        self.Class_Novel.novel['config'] = novel_config
        return

    def save(self, full_save=False, title=None):
        # 保存的格式 self.saved_novel
        for title in list(self.Class_Novel.novel["chapters"].keys()):
            # 格式化
            if self.saved_novel.get(title, None) is None:
                self.saved_novel[title] = {}
                chapter = self.Class_Novel.novel["chapters"][title]
                # 格式: 标题 + '\n\t' + 字数 + '\t' + 更新时间 + '\n' + 内容 + '\n\n'
                content = re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter['content'])   # 去掉图片占位字符串
                formatted = (                                       # 格式化文本
                    f"{title}\n    "
                    f"{chapter['count_word']}    "
                    f"{chapter['update']}\n\n"
                    f"{content}\n\n"
                )
                size = len(formatted.encode('utf-8'))               # 文本大小
                self.saved_novel[title] = {
                    "img": {
                        'saved': False,
                        'item': self.Class_Novel.novel["chapters"][title]['img_item']
                    },
                    "txt": {
                        'saved': False,
                        'text': formatted,
                        'size': size,
                    },
                    "epub": {
                        'saved': False
                    },
                    "html": {
                        'saved': False
                    }
                }

        # 整理
        sorted_saved_novel = {}
        for title in self.Class_Novel.all_title_list:
            if title in self.saved_novel:
                sorted_saved_novel[title] = self.saved_novel[title]

        # 保留不在 all_title_list 中的标题
        for title, content in self.saved_novel.items():
            if title not in self.Class_Novel.all_title_list:
                sorted_saved_novel[title] = content

        # 保存
        for file_format in self.Class_Config.Save_method.keys():
            match file_format:
                case 'json':
                    if self.save_config[file_format].get('enable', True):
                        self._json_save()
                case 'txt':
                    if self.save_config[file_format].get('enable', True):
                        self._txt_save()
                case 'epub':
                    if self.save_config[file_format].get('enable', True):
                        self._epub_save()
                case 'html':
                    if self.save_config[file_format].get('enable', True):
                        self._html_save()

    def _json_save(self):

        base_dir = self.Class_Config.Base_dir
        os.makedirs(base_dir, exist_ok=True)
        # 根JSON文件名
        file_name = self.Class_Novel.novel["info"]["name"] + ".json"
        # 更新最后一次控制时间
        timestamp = time.time()
        self.Class_Novel.novel["config"]["Last_control_timestamp"] = timestamp

        # 保存JSON文件
        json_content = json.dumps(self.Class_Novel.novel, ensure_ascii=False, indent=4)
        with open(os.path.join(base_dir, file_name), 'w', encoding='utf-8') as f:       # 根JSON文件
            f.write(json_content)

        with open(self.save_config['json']['filepath'], 'w', encoding='utf-8') as f:
            f.write(json_content)

        """执行保存操作"""
        self.Class_Config.save_config()

        # 保存图片
        for title in self.saved_novel.keys():
            # 检查当前章节是否保存了图片
            if not self.saved_novel[title]['img']['saved']:
                img_item = self.saved_novel[title]['img']['item']
                # 当有图片数据时
                if img_item:
                    # 避免title非法导致无法保存
                    formatted_title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', title)
                    img_title_dir = self.save_config['json']['img_dir'] / formatted_title \
                        if formatted_title != '小说信息' else self.save_config['json']['img_dir'] / "封面图片"
                    img_title_dir.mkdir(parents=True, exist_ok=True)        # 确保目录存在
                    for alt, data in img_item.items():
                        img_alt_path = img_title_dir / f"{alt}.png"         # 以图片描述为文件名
                        img_data = base64.b64decode(data[21:])              # 纯base64数据
                        # 保存
                        with open(img_alt_path, 'wb') as f:
                            f.write(img_data)
                # 不再读取img_item
                self.saved_novel[title]['img']['saved'] = True

    def _txt_save(self):
        gap = self.save_config['txt'].get('gap', -1)
        if gap > 1:
            # 获取所有章节标题的有序列表
            chapter_titles = list(self.saved_novel.keys())

            for title in chapter_titles:
                # 检查当前章节是否未保存
                if not self.saved_novel[title]['txt']['saved']:
                    # 定位当前章节在列表中的索引
                    tp = chapter_titles.index(title)
                    # 计算分组ID
                    id_ = tp // gap

                    # 确定当前分组包含的章节范围
                    start_idx = id_ * gap
                    end_idx = min((id_ + 1) * gap, len(chapter_titles))

                    # 生成文件名
                    file_name = f"{start_idx}-{end_idx - 1}.txt"

                    # 获取当前分组的所有标题
                    gap_title_list = chapter_titles[start_idx:end_idx]

                    # 合并当前分组的所有文本内容
                    text = ''
                    for chunk_title in gap_title_list:
                        text += self.saved_novel[chunk_title]['txt']['text']
                        # 标记为已保存
                        self.saved_novel[chunk_title]['txt']['saved'] = True

                    # 确保目录存在
                    os.makedirs(self.save_config['txt']['gap_dir'], exist_ok=True)

                    file_path = os.path.join(self.save_config['txt']['gap_dir'], file_name)
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(text)

        elif gap == 1:
            for title in self.saved_novel.keys():
                # 检查当前章节是否未保存
                if not self.saved_novel[title]['txt']['saved']:
                    # 标题合法化
                    formatted_title = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', title)
                    with open(os.path.join(self.save_config['txt']['gap_dir'], f"{formatted_title}.txt"), 'r', encoding='utf-8') as f:
                        f.write(self.saved_novel[title]['txt']['text'])
                    self.saved_novel[title]['txt']['saved'] = True

        elif gap == 0:
            text = ''
            # 合并成为单文本
            for title in list(self.saved_novel.keys()):
                text += self.saved_novel[title]['txt']['text']
            with open(self.save_config['txt']['filepath'], 'w', encoding='utf-8') as f:
                f.write(text)

        max_filesize = self.save_config['txt'].get('max_filesize', -1)
        if max_filesize > 0:
            text = ''
            size = 0

            for title in self.saved_novel.keys():
                size += self.saved_novel[title]['txt']['size']
                # 达到临界值
                if size > max_filesize*1024:
                    # 已经保存过的text不再重新保存
                    if text in self.size_texts:
                        continue
                    else:
                        self.size_texts.append(text)
                        current_id = len(self.size_texts)
                        with open(os.path.join(self.save_config['txt']['size_dir'], f"{current_id}.txt"), 'w', encoding='utf-8') as f:
                            f.write(text)
                        text = ''
                        size = 0
                else:
                    text += self.saved_novel[title]['txt']['text']
            if text:
                with open(os.path.join(self.save_config['txt']['size_dir'], f"{len(self.size_texts)+1}.txt"), 'w', encoding='utf-8') as f:
                    f.write(text)

        pass

    def _epub_save(self):
        return

    def _html_save(self):
        # 此html阅读器蓝本由deepseek及豆包调校后提供

        with open(r'data\Local\template.html', encoding='utf-8') as f:
            template = f.read()
        # html路径
        html_path = self.save_config['html']['dir'] / f'{self.novel_name}.html'
        noveldata = json.dumps(self.Class_Novel.novel, ensure_ascii=False, indent=4)
        template = template.replace("<&?NovelData!&>", noveldata)   # 替换为json
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(template)
        return
