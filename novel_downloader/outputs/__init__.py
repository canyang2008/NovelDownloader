import os
import re
import platform
from pathlib import Path

def dir_transform(path:str, user, group, name):  # 特殊路径转化
    path = path.replace('<User>',user) if '<User>' in path else path
    path = path.replace('<Group>',group) if '<Group>' in path else path
    path = path.replace('<Name>',name) if '<Name>' in path else path
    return path

def sanitize_name(filename, replace_with="_"):
    current_os = platform.system()
    if current_os == "Windows":
        illegal_chars = r'[<>:"/\\|?*\x00]'
        cleaned = re.sub(illegal_chars, replace_with, filename)
        cleaned = cleaned.rstrip('. ')
        windows_reserved = [
            "CON", "PRN", "AUX", "NUL",
            "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
            "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
        ]
        name_without_ext = os.path.splitext(cleaned)[0].upper()
        if name_without_ext in windows_reserved:
            cleaned = f"_{cleaned}"
    else:
        illegal_chars = r'[/\x00]'
        cleaned = re.sub(illegal_chars, replace_with, filename)
    cleaned = cleaned.strip()
    max_length = 255 if current_os != "Windows" else 260
    if len(cleaned) > max_length:
        name, ext = os.path.splitext(cleaned)
        cleaned = name[:max_length - len(ext) - 10] + ext

    return cleaned
