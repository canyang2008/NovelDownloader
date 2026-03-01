import os
from dataclasses import dataclass, field


@dataclass
class SaveFormatConfig:
    """保存格式配置基类"""
    enable: bool = True
    file_name: str|None = None
    output_dir: str = os.path.join("data","Bookstore","<User>","<Group>","<Name>")

@dataclass
class BaseSaveConfig(SaveFormatConfig):
    """小说根数据保存独立配置"""
    name = "base"
    output_dir: str = os.path.join("data","Local","<User>","json")

@dataclass
class JsonSaveConfig(SaveFormatConfig):
    """JSON保存配置"""
    name = "json"
    indent:int = 4
    save_interval:int = 3
    ensure_ascii: bool = False
    extension: str = ".json"

@dataclass
class ImgSaveConfig(SaveFormatConfig):
    """图片保存配置"""
    name = "img"
    output_dir: str = os.path.join("data","Bookstore","<User>","<Group>","<Name>","Img")
    method:int = 0              # 未应用
    extension:str = ".png"       # 未应用

@dataclass
class TxtSaveConfig(SaveFormatConfig):
    """TXT保存配置"""
    name = "txt"
    chapters_per_file: int = 0
    file_size: float = -1
    encoding: str = "utf-8"
    extension: str = ".txt"

@dataclass
class HtmlSaveConfig(SaveFormatConfig):
    """HTML保存配置"""
    name = "html"
    one_file: bool = True
    template: str = "default"   # 未应用
    extension: str = ".html"    # 未应用

@dataclass
class EpubSaveConfig(SaveFormatConfig):
    """EPUB保存配置"""
    name = "epub"
    css_style: str = "default"
    include_toc: bool = True
    extension: str = ".epub"

@dataclass
class SaveMethodConfig:
    """保存方法配置"""
    base: BaseSaveConfig = field(default_factory=BaseSaveConfig)
    json: JsonSaveConfig = field(default_factory=JsonSaveConfig)
    txt: TxtSaveConfig = field(default_factory=TxtSaveConfig)
    html: HtmlSaveConfig = field(default_factory=HtmlSaveConfig)
    epub: EpubSaveConfig = field(default_factory=EpubSaveConfig)
    img: ImgSaveConfig = field(default_factory=ImgSaveConfig)
