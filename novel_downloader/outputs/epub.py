import os
import re
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field

try:
    from ebooklib import epub
except ImportError:
    raise ImportError("Please install ebooklib: pip install ebooklib")

from novel_downloader.outputs.base import Output
from novel_downloader.models.save import EpubSaveConfig

class EPUBOutput(Output):
    """EPUB输出格式，支持多次save和乱序章节"""

    def __init__(self, save_config: EpubSaveConfig):
        super().__init__(save_config)
        self.save_config: EpubSaveConfig = save_config
        self.order_chapter_dict: Dict[int, Any] = {}  # order -> Chapter对象
        self.novel = None  # 需要外部赋值

    def save(self, chapters, **kwargs):
        return None
        """保存一批章节，更新缓存并重新生成EPUB文件"""
        if self.save_config.enable is not None and not self.save_config.enable:
            return None

        if self.novel is None:
            raise ValueError("Novel object must be set before calling save()")

        # 更新缓存
        for chapter in chapters:
            if chapter is not None:
                self.order_chapter_dict[chapter.order] = chapter

        # 重新生成EPUB文件
        self._write_epub()

    def close(self):
        """无需特殊关闭操作"""
        pass

    # ---------- 私有方法 ----------

    def _write_epub(self):
            """根据当前缓存生成EPUB文件"""
            output_dir = self.save_config.output_dir
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, self.save_config.file_name + self.save_config.extension)

            book = epub.EpubBook()
            # ...（元数据、封面、CSS 部分不变）...

            # 排序章节
            sorted_orders = sorted(self.order_chapter_dict.keys())
            sorted_chapters = [self.order_chapter_dict[order] for order in sorted_orders]

            epub_chapters = []
            img_filenames = {}  # (chapter.order, idx) -> (filename, real_desc)

            # 第一遍：处理图片
            for chapter in sorted_chapters:
                for idx, (img_desc, img_data) in enumerate(chapter.images):
                    ext = self._guess_image_ext(img_data)
                    filename = f'images/img_{chapter.order}_{idx}{ext}'
                    real_desc = self._parse_image_desc(img_desc)

                    img_item = epub.EpubImage()
                    img_item.file_name = filename
                    img_item.media_type = self._guess_media_type(ext)
                    img_item.content = img_data
                    book.add_item(img_item)

                    img_filenames[(chapter.order, idx)] = (filename, real_desc)

            # 第二遍：生成章节HTML
            for chapter in sorted_chapters:
                # 确保标题非空
                title = chapter.title if chapter.title and chapter.title.strip() else "无标题"

                # 构建正文HTML
                paragraphs = chapter.content.strip().split('\n') if chapter.content else []
                html_body = ''.join(f'<p>{p}</p>' for p in paragraphs if p)

                # 添加图片
                if chapter.images:
                    html_body += '<div class="chapter-images">'
                    for idx, (img_desc, img_data) in enumerate(chapter.images):
                        filename, real_desc = img_filenames.get((chapter.order, idx), (None, None))
                        if filename is None:
                            continue
                        alt_text = real_desc if real_desc else ""
                        img_tag = f'<img src="{filename}" alt="{alt_text}"/>'
                        html_body += img_tag
                        if real_desc:
                            html_body += f'<p class="image-caption">{real_desc}</p>'
                    html_body += '</div>'

                # 确保至少有一个非空元素
                if not html_body.strip():
                    html_body = '<p>&#160;</p>'  # 使用不间断空格作为占位

                # 完整XHTML
                html = f"""<?xml version='1.0' encoding='utf-8'?>
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="style/default.css"/>
    </head>
    <body>
        <h1>{title}</h1>
        {html_body}
    </body>
    </html>"""

                # 额外验证：使用lxml解析，确保不会导致空文档错误
                try:
                    from lxml import html as lxml_html
                    lxml_html.fromstring(html)
                except Exception as e:
                    # 如果解析失败，使用一个安全的后备内容
                    print(f"警告：章节 {title} (order={chapter.order}) HTML解析失败，使用安全内容。错误：{e}")
                    html = f"""<?xml version='1.0' encoding='utf-8'?>
    <!DOCTYPE html>
    <html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <title>{title}</title>
        <link rel="stylesheet" type="text/css" href="style/default.css"/>
    </head>
    <body>
        <h1>{title}</h1>
        <p>本章内容无法正常显示，请查看原始数据。</p>
    </body>
    </html>"""

                chap_item = epub.EpubHtml(
                    title=title,
                    file_name=f'chapter_{chapter.order}.xhtml',
                    lang='zh-CN'
                )
                # 添加CSS样式
                css_content = self._get_css_content()
                style_item = None  # ✅ 初始化变量，避免未定义
                if css_content:
                    style_item = epub.EpubItem(
                        uid="style",
                        file_name="style/default.css",
                        media_type="text/css",
                        content=css_content
                    )
                    book.add_item(style_item)
                chap_item.content = html
                if style_item:
                    chap_item.add_item(style_item)
                book.add_item(chap_item)
                epub_chapters.append(chap_item)

            # 设置spine和目录
            book.spine = ['nav'] + epub_chapters
            if self.save_config.include_toc and epub_chapters:
                book.toc = epub_chapters
                book.add_item(epub.EpubNcx())
                book.add_item(epub.EpubNav())

            # 写入文件（捕获异常）
            try:
                epub.write_epub(file_path, book, {})
            except Exception as e:
                print(f"EPUB写入失败：{e}")
                raise  # 可选择抛出或忽略

    def _parse_image_desc(self, desc: str) -> str:
        """解析图片描述，返回真正的描述文字，若无则返回空字符串"""
        # 格式: "(n) 真正的图片描述"
        match = re.match(r'^\(\d+\)\s*(.*)$', desc)
        if match:
            real_desc = match.group(1).strip()
            return real_desc
        return ""

    def _guess_image_ext(self, data: bytes) -> str:
        """根据图片二进制数据猜测扩展名"""
        if data.startswith(b'\xff\xd8'):
            return '.jpg'
        elif data.startswith(b'\x89PNG\r\n\x1a\n'):
            return '.png'
        elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
            return '.gif'
        elif data.startswith(b'BM'):
            return '.bmp'
        elif data.startswith(b'RIFF') and data[8:12] == b'WEBP':
            return '.webp'
        else:
            return '.jpg'  # 默认

    def _guess_media_type(self, ext: str) -> str:
        """根据扩展名返回MIME类型"""
        ext = ext.lower()
        if ext in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        elif ext == '.png':
            return 'image/png'
        elif ext == '.gif':
            return 'image/gif'
        elif ext == '.bmp':
            return 'image/bmp'
        elif ext == '.webp':
            return 'image/webp'
        else:
            return 'application/octet-stream'

    def _get_css_content(self) -> Optional[str]:
        """根据配置返回CSS内容"""
        if self.save_config.css_style == 'default':
            return """
body {
    font-family: 'Times New Roman', Times, serif;
    margin: 5%;
    text-align: justify;
}
h1 {
    text-align: center;
    font-size: 1.8em;
    margin-bottom: 1em;
}
p {
    text-indent: 2em;
    line-height: 1.5;
    margin: 0.5em 0;
}
.chapter-images {
    margin-top: 2em;
    text-align: center;
}
.chapter-images img {
    max-width: 100%;
    height: auto;
    margin: 1em 0;
}
.image-caption {
    font-size: 0.9em;
    color: #666;
    text-align: center;
    margin-top: -0.5em;
    margin-bottom: 1.5em;
}
"""
        return None