import re
import time
import os
import html
from typing import Any, Iterable, List, Tuple

from ebooklib import epub
from novel_downloader.outputs.base import Output
from novel_downloader.models.save import EpubSaveConfig


class EPUBOutput(Output):
    """EPUB输出格式，支持多次save，每次调用都立即生成EPUB文件"""
# AI制作
    def close(self):
        pass

    def __init__(self, save_config: EpubSaveConfig):
        super().__init__(save_config)
        self.order_chapter_dict: dict[int, Any] = {}  # order -> Chapter对象

    def save(self, chapters: Iterable[Any], **kwargs):
        return None
        """保存传入的章节，并立即生成/更新EPUB文件"""
        for chapter in chapters:
            self.order_chapter_dict[chapter.order] = chapter
        # 每次调用save都生成EPUB（覆盖原文件）
        self._generate_epub()

    def _generate_epub(self):
        """基于当前累积的章节生成EPUB文件并保存"""
        novel = self.novel
        book = epub.EpubBook()

        # 设置唯一标识（可用URL的哈希值）
        book.set_identifier(f'id_{hash(novel.url)}')
        book.set_title(novel.name)
        book.set_language('zh')
        if novel.author:
            book.add_author(novel.author)

        # 添加小说信息页
        info_chapter = self._create_info_chapter()
        book.add_item(info_chapter)
        info_id = info_chapter.id

        # 添加CSS
        css = self._create_css()
        book.add_item(css)

        # 添加封面图片
        if novel.cover_image_data:
            cover = epub.EpubImage()
            cover.file_name = 'cover.jpg'
            cover.media_type = 'image/jpeg'
            cover.content = novel.cover_image_data
            book.add_item(cover)
            book.set_cover("cover.jpg", cover.content)  # set_cover 内部处理，无需手动加入spine

        # 处理章节
        sorted_chapters = sorted(self.order_chapter_dict.items(), key=lambda x: x[0])
        chapters = [ch for _, ch in sorted_chapters]

        epub_chapters = []
        all_images = []

        for ch in chapters:
            epub_ch, images = self._chapter_to_epub(ch)
            book.add_item(epub_ch)  # 立即添加章节到书
            epub_chapters.append(epub_ch)  # 保存引用，用于后续目录和spine
            all_images.extend(images)

        # 添加所有图片
        for img in all_images:
            book.add_item(img)

        # 设置spine（按阅读顺序）
        spine_items = ['nav']
        if info_chapter:
            spine_items.append(info_id)  # 使用 id 字符串
        for epub_ch in epub_chapters:
            spine_items.append(epub_ch.id)  # 使用 id 字符串

        book.spine = spine_items

        # 设置目录（目录可以接受对象，也可用id，但对象更直观）
        if self.save_config.include_toc:
            book.toc = []
            if info_chapter:
                book.toc.append(epub.Section('前言', [info_chapter]))
            for epub_ch in epub_chapters:
                book.toc.append(epub_ch)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

        # 确定输出路径
        output_dir = self.save_config.output_dir
        file_name = self.save_config.file_name
        if not file_name:
            safe_name = re.sub(r'[\\/*?:"<>|]', '', novel.name)
            file_name = safe_name or 'novel'
        full_path = os.path.join(output_dir, file_name + self.save_config.extension)

        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 写入EPUB文件（覆盖旧文件）
        epub.write_epub(full_path, book, {})

        # 注意：不清空字典，保留已收集章节以便下次继续添加

    def _create_info_chapter(self) -> epub.EpubHtml:
        """生成小说信息页"""
        info_text = self._generate_info_text()
        info_text = html.escape(info_text)
        html_content = f"<div>{info_text.replace(chr(10), '<br/>')}</div>"
        full_html = f'''
        <html>
        <head>
            <link rel="stylesheet" type="text/css" href="style.css"/>
        </head>
        <body>
            <h1>小说信息</h1>
            {html_content}
        </body>
        </html>
        '''
        chapter = epub.EpubHtml(title='小说信息', file_name='info.xhtml', lang='zh')
        chapter.content = full_html
        return chapter

    def _create_css(self) -> epub.EpubItem:
        """生成CSS样式文件"""
        style = epub.EpubItem(uid='style', file_name='style.css', media_type='text/css')
        if self.save_config.css_style == 'default':
            style.content = '''
                body { font-family: sans-serif; margin: 5%; }
                h1 { text-align: center; }
                p { text-indent: 2em; }
                .image-container { text-align: center; margin: 1em 0; }
                .image-caption { font-size: 0.9em; color: gray; text-indent: 0; }
            '''
        else:
            style.content = ''
        return style

    def _chapter_to_epub(self, chapter: Any) -> Tuple[epub.EpubHtml, List[epub.EpubImage]]:
        """将单个Chapter转换为EpubHtml对象，并返回关联的图片列表"""
        # 1. 去除图片占位符
        content = re.sub(r'<&!img\?group_id=\d+/!&>', '', chapter.content)
        # 2. 转义HTML
        content = html.escape(content)
        # 3. 将文本段落用<p>包裹
        paragraphs = content.split('\n')
        html_content = ''
        for p in paragraphs:
            if p.strip():
                html_content += f'<p>{p}</p>\n'
            else:
                html_content += '<br/>\n'

        # 4. 处理图片
        images_html = ''
        images = []
        for i, (desc, data) in enumerate(chapter.images, start=1):
            alt = self._get_image_alt(desc)
            alt_escaped = html.escape(alt)

            mime, ext = self._get_image_info(data)
            img_filename = f'images/ch{chapter.order}_{i}{ext}'

            img_item = epub.EpubImage()
            img_item.file_name = img_filename
            img_item.media_type = mime
            img_item.content = data
            images.append(img_item)

            img_tag = f'<img src="{img_filename}" alt="{alt_escaped}" />'
            if alt:
                caption = f'<p class="image-caption">{alt_escaped}</p>'
                images_html += f'<div class="image-container">{img_tag}{caption}</div>\n'
            else:
                images_html += f'<div class="image-container">{img_tag}</div>\n'

        # 5. 组装完整HTML
        title = html.escape(chapter.title)
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(chapter.timestamp))
        full_html = f'''
        <html>
        <head>
            <link rel="stylesheet" type="text/css" href="style.css"/>
        </head>
        <body>
            <h1>{title}</h1>
            <p>更新字数：{chapter.count} 更新时间：{timestamp_str}</p>
            <div class="content">
                {html_content}
            </div>
            <div class="images-section">
                {images_html}
            </div>
        </body>
        </html>
        '''

        epub_ch = epub.EpubHtml(title=title, file_name=f'chapter_{chapter.order}.xhtml', lang='zh')
        epub_ch.content = full_html
        return epub_ch, images

    @staticmethod
    def _get_image_alt(desc: str) -> str:
        """从图片描述字符串中提取alt文本（去除序号部分）"""
        parts = desc.split(' ', 1)
        if len(parts) == 2:
            return parts[1].strip()
        return ""

    @staticmethod
    def _get_image_info(data: bytes) -> Tuple[str, str]:
        """根据图片数据猜测MIME类型和文件扩展名"""
        if data.startswith(b'\xff\xd8'):
            return 'image/jpeg', '.jpg'
        elif data.startswith(b'\x89PNG'):
            return 'image/png', '.png'
        elif data.startswith(b'GIF87a') or data.startswith(b'GIF89a'):
            return 'image/gif', '.gif'
        else:
            return 'image/jpeg', '.jpg'

    def _generate_info_text(self) -> str:
        """生成小说信息文本（复用父类或自行实现）"""
        novel = self.novel
        return (
            f"小说名：{novel.name}\n作者：{novel.author}\n"
            f"简介：{novel.description}\n标签：{' '.join(novel.tags)}\n"
            f"字数：{novel.count}\n"
            f"最后更新：{novel.last_update_chapter} "
            f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(novel.last_update_time))}\n"
            f"链接：{novel.url}\n\n"
        )