import base64
import copy
import json
import math
import os
import re
import shutil
from pathlib import Path

import msgpack


class Save:
    def __init__(self, logger_):

        self.logger = logger_
        self.size_text = None
        self.gap_size_idx = None
        self.size_title_lists = []
        self.txt_chunk_keys = None
        self.full_save = None
        self.save_config = None
        self.Class_Novel = None
        self.Class_Config = None

    def config(self, Class_Novel, Class_Config):
        self.Class_Novel = Class_Novel
        self.Class_Config = Class_Config
        # 全局：小说名字和小说信息文本
        self.save_config = copy.deepcopy(self.Class_Config.Save_method)
        self.save_config['novel_name'] = novel_name = self.Class_Novel.novel['info']['name']
        novel_info = self.Class_Novel.novel['info']
        novel_abstract = novel_info['abstract'].replace('\n', '\n\t')
        if 'txt' in self.save_config.keys():
            self.save_config['info_text'] = (  # 生成小说信息文本
                f"小说名：{novel_name}\n作者：{novel_info['author']}\n"
                f"简介：{novel_abstract}\n标签：{novel_info['label']}\n"
                f"字数：{novel_info['count_word']}\n最后更新：{novel_info['last_update']}\n"
                f"链接：{novel_info['url']}\n\n"
            )
        for file_format, config in self.save_config.items():
            if file_format in ['novel_name', 'info_text']:
                continue
            # === 配置准备 ===
            path_parts = list(Path(self.Class_Config.Save_method[file_format]['dir']).parts)
            if '<User>' in path_parts:
                tp = path_parts.index('<User>')
                path_parts[tp] = self.Class_Config.User
            if '<Group>' in path_parts:
                tp = path_parts.index('<Group>')
                path_parts[tp] = self.Class_Config.Group
            if '<Name>' in path_parts:
                tp = path_parts.index('<Name>')
                path_parts[tp] = novel_name
            path = path_parts[0] + '\\'.join(path_parts[1:]) if os.path.isabs(
                self.Class_Config.Save_method[file_format]['dir']) else '\\'.join(path_parts)
            self.Class_Config.Save_method[file_format]['dir'] = config['dir'] = path

            if file_format == 'json':
                path_parts = list(Path(self.Class_Config.Save_method[file_format]['img_dir']).parts)
                if '<User>' in path_parts:
                    tp = path_parts.index('<User>')
                    path_parts[tp] = self.Class_Config.User
                if '<Group>' in path_parts:
                    tp = path_parts.index('<Group>')
                    path_parts[tp] = self.Class_Config.Group
                if '<Name>' in path_parts:
                    tp = path_parts.index('<Name>')
                    path_parts[tp] = novel_name
                path = path_parts[0] + '\\'.join(path_parts[1:]) if os.path.isabs(
                    self.Class_Config.Save_method[file_format]['img_dir']) else '\\'.join(path_parts)
                self.Class_Config.Save_method[file_format]['img_dir'] = config['img_dir'] = path
                # 处理目录路径
                config['img_dir'] = Path(config.get('img_dir', Path(__file__).parent)).resolve()
                # 确保目录存在
                config['img_dir'].mkdir(parents=True, exist_ok=True)

            # 设置默认文件名
            if config.get('name') == 'name_default':
                config['name'] = f"{novel_name}.{file_format}"
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

        return

    def save(self, full_save=False, title=None):
        for file_format in self.Class_Config.Save_method.keys():
            match file_format:
                case 'json':
                    self.json_save(full_save)
                case 'txt':
                    self.txt_save(full_save, title)
                case 'epub':
                    self.epub_save(full_save, title)
                case 'html':
                    self.html_save(full_save, title)

    def json_save(self, full_save=False):

        # 根JSON保存
        root_path = os.path.join(os.getenv("LOCALAPPDATA"), "CyNovelbase",
                                 "data", self.Class_Config.Main_user, "json",
                                 self.Class_Novel.novel['info']['name'] + '.json')
        os.makedirs(os.path.dirname(root_path), exist_ok=True)
        with open(root_path, 'wb') as f:
            msgpack.dump(self.Class_Novel.novel, f)

        # 保存JSON文件
        json_content = json.dumps(self.Class_Novel.novel, ensure_ascii=False, indent=2)
        with open(self.save_config['json']['filepath'], 'w', encoding='utf-8') as f:
            f.write(json_content)

        """执行保存操作"""
        self.Class_Config.add_url_config(name=self.save_config['novel_name'],
                                         state=self.Class_Novel.novel['info']['label'][:3])  # 更新配置文件
        self.Class_Config.save_config()

        if full_save:  # 以保存所有的图片
            for title in self.Class_Novel.novel['chapters'].keys():
                if self.Class_Novel.novel['chapters'][title]['img_item']:
                    self.Class_Novel.img_items[title] = self.Class_Novel.novel['chapters'][title]['img_item']

        # 保存图片
        for img_alt, desc_imgurl in self.Class_Novel.img_items.items():
            img_alt = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', img_alt)
            img_dir = self.save_config['json']['img_dir'] / img_alt
            img_dir.mkdir(parents=True, exist_ok=True)
            for desc, base64_data in desc_imgurl.items():
                img_path = img_dir / f'{desc}.png'
                img_data = base64.b64decode(base64_data[21:])
                with open(img_path, 'wb') as f:
                    f.write(img_data)
        self.Class_Novel.img_items.clear()  # 删除已保存的图片链接

    def txt_save(self, full_save=False, current_title=None):

        gap = self.save_config['txt'].get('gap', -1)
        if gap > 0:
            self.save_config['txt']['gap_dir'] = self.save_config['txt']['dir']
            if self.txt_chunk_keys is None:
                self.txt_chunk_keys = []
                if Path(self.Class_Config.Save_method['txt']['dir']).resolve() == Path(
                        self.Class_Config.Save_method['json']['dir']).resolve():  # 如果txt和json的目录相同，再次创建目录
                    self.save_config['txt']['gap_dir'] = self.save_config['txt']['dir'] / f'txt gap={gap}'
                    # 确保目录存在
                    self.save_config['txt']['gap_dir'].mkdir(parents=True, exist_ok=True)
                # 保存小说信息
                info_path = self.save_config['txt']['gap_dir'] / '小说信息.txt'

                with open(info_path, 'w', encoding='utf-8') as f:
                    f.write(self.save_config['info_text'])

            # 获取章节标题列表（保持原始顺序）
            chapters = self.Class_Novel.novel['chapters']
            titles = list(chapters.keys())
            total_chapters = len(titles)

            # 计算需要分成的块数
            num_chunks = math.ceil(total_chapters / gap)

            for i in range(num_chunks):

                # 计算当前块的起始和结束索引（从1开始的序号）
                start_idx = i * gap + 1
                end_idx = (i + 1) * gap
                chunk_key = f"{start_idx}-{end_idx}"
                if gap == 1: chunk_key = titles[start_idx - 1]
                chunk_key = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', chunk_key)
                if chunk_key not in self.txt_chunk_keys:
                    # 获取当前块包含的章节标题
                    start = i * gap
                    end = min(start + gap, total_chapters)
                    chunk_titles = titles[start:end]

                    # 格式化当前块的所有章节内容
                    chunk_content = ""
                    for title in chunk_titles:
                        chapter = chapters[title]
                        # 格式: 标题 + '\n\t' + 字数 + '\t' + 更新时间 + '\n' + 内容 + '\n\n'
                        content = re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter['content'])
                        formatted = (
                            f"{title}\n\t"
                            f"{chapter['count_word']}\t"
                            f"{chapter['update']}\n\n"
                            f"{content}\n\n"
                        )
                        chunk_content += formatted
                    with open(self.save_config['txt']['gap_dir'] / (chunk_key + '.txt'), 'w', encoding='utf-8') as f:
                        f.write(chunk_content)
                    if gap == len(chunk_titles):
                        self.txt_chunk_keys.append(chunk_key)

        elif gap == 0:  # 不分块保存
            if full_save:  # 重写
                all_titles = list(self.Class_Novel.novel['chapters'].keys())
                full_text = self.save_config['info_text']
                for title in all_titles:
                    chapter = self.Class_Novel.novel['chapters'][title]
                    content = re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter['content'])
                    formatted = (
                        f"{title}\n\t"
                        f"{chapter['count_word']}\t"
                        f"{chapter['update']}\n\n"
                        f"{content}\n\n"
                    )
                    full_text += formatted

                with open(self.save_config['txt']['filepath'], 'w', encoding='utf-8') as f:
                    f.write(full_text)

            else:  # 追加

                chapter = self.Class_Novel.novel['chapters'][current_title]
                content = re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter['content'])
                formatted = (
                    f"{current_title}\n\t"
                    f"{chapter['count_word']}\t"
                    f"{chapter['update']}\n\n"
                    f"{content}\n\n"
                )
                if current_title == self.Class_Novel.down_title_list[0]:
                    formatted = self.save_config['info_text'] + formatted

                with open(self.save_config['txt']['filepath'], 'a', encoding='utf-8') as f:
                    f.write(formatted)

        max_filesize = self.Class_Config.Save_method['txt'].get('max_filesize', 0)
        if max_filesize > 0:
            self.save_config['txt']['fize_dir'] = self.save_config['txt']['dir']
            if Path(self.Class_Config.Save_method['txt']['dir']).resolve() == Path(
                    self.Class_Config.Save_method['json']['dir']).resolve():  # 如果txt和json的目录相同，再次创建目录
                self.save_config['txt']['fize_dir'] = self.save_config['txt']['dir'] / f'txt {max_filesize}KB'
                # 确保目录存在
                self.save_config['txt']['fize_dir'].mkdir(parents=True, exist_ok=True)
                # 保存小说信息
                info_path = self.save_config['txt']['fize_dir'] / '小说信息.txt'
                with open(info_path, 'w', encoding='utf-8') as f:
                    f.write(self.save_config['info_text'])
            if full_save:
                text = ''
                idx = 1
                for title in self.Class_Novel.novel['chapters'].keys():
                    chapter = self.Class_Novel.novel['chapters'][title]
                    content = re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter['content'])
                    formatted = (
                        f"{current_title}\n\t"
                        f"{chapter['count_word']}\t"
                        f"{chapter['update']}\n\n"
                        f"{content}\n\n"
                    )
                    text += formatted
                    if len(text.encode('utf-8')) >= max_filesize * 1024:
                        with open(self.save_config['txt']['fize_dir'] / f"({idx}).txt", 'w', encoding='utf-8') as f:
                            f.write(text)
                            text = ''  # 清空文本内容
                            idx += 1
                else:  # 如果最后还有剩余内容
                    if text:
                        with open(self.save_config['txt']['fize_dir'] / f"{idx}.txt", 'w', encoding='utf-8') as f:
                            f.write(text)

            else:
                if self.gap_size_idx is None:
                    self.size_text = ''
                    self.gap_size_idx = 0  # 初始化

                chapter = self.Class_Novel.novel['chapters'][current_title]
                content = re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter['content'])
                formatted = (
                    f"{current_title}\n\t"
                    f"{chapter['count_word']}\t"
                    f"{chapter['update']}\n\n"
                    f"{content}\n\n"
                )
                self.size_text += formatted
                with open(self.save_config['txt']['fize_dir'] / f"({self.gap_size_idx}).txt", 'w',
                          encoding='utf-8') as f:
                    f.write(self.size_text)
                if len(self.size_text.encode('utf-8')) >= max_filesize * 1024:
                    self.size_text = ''  # 清空文本内容
                    self.gap_size_idx += 1

        return True

    def epub_save(self, full_save=False, title=None):
        return

    def html_save(self, full_save=False, title=None):
        # 此html阅读器蓝本由deepseek及豆包被调校后提供

        with open(r'data\Record\template.html', encoding='utf-8') as f:
            template = f.read()
        html_path = self.save_config['html']['dir'] / 'index.html'
        if not self.save_config['html']['one_file']:
            self.save_config['html']['dir'] = self.save_config['html']['dir'] / 'html'
            img_dir = self.save_config['html']['dir'] / 'Img'
            shutil.copytree(self.save_config['json']['img_dir'], img_dir, dirs_exist_ok=True)
            if not full_save:
                img_item = self.Class_Novel.novel['chapters'][title]['img_item']
                for desc, data in img_item.items():
                    data = str(img_dir / title / desc) + '.png'
                    img_item[desc] = os.path.relpath(data, self.save_config['html']['dir'])
                self.Class_Novel.novel['chapters'][title]['img_item'] = img_item
                noveldata = json.dumps(self.Class_Novel.novel, ensure_ascii=False, indent=2)
                template = template.replace("<&?NovelData!&>", noveldata)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(template)

            else:
                for title in self.Class_Novel.novel['chapters'].keys():
                    img_item = self.Class_Novel.novel['chapters'][title]['img_item']
                    for desc, data in img_item.items():
                        data = str(img_dir / title / desc) + '.png'
                        img_item[desc] = os.path.relpath(data, self.save_config['html']['dir'])
                noveldata = json.dumps(self.Class_Novel.novel, ensure_ascii=False, indent=2)
                template = template.replace("<&?NovelData!&>", noveldata)
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(template)

        else:
            noveldata = json.dumps(self.Class_Novel.novel, ensure_ascii=False, indent=2)
            template = template.replace("<&?NovelData!&>", noveldata)
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(template)
            pass
        return
