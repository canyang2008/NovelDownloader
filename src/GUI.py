# -*- coding: utf-8 -*-
import logging
import os
import re
import sys
import traceback
from datetime import datetime
from tkinter import *

from RunDriver import RunDriver
from Save import Save
from SetConfig import SetConfig


class NovelDownloader:

    def __init__(self, logger_):
        self.logger = logger_
        self.select = None
        self.download_url = None
        self.range = None
        self.downargs = {}
        self.Class_Config = SetConfig()
        self.Class_Driver = RunDriver(logger_)
        self.Class_Novel = None
        self.Class_Save = Save(logger_)
        self.Class_Novel = None
        return


root = Tk()
root.title("小说下载器 | NovelDownloader")
root.geometry("800x600")
root.resizable(False, False)    # 设定不能改变窗口的宽和高尺寸
main_frame = Frame(root)    # 主框架
url_input_prompt = Label(main_frame, text="URL:", relief="sunken", font=("黑体", 18)) # 提示
url_input_prompt.pack(side="left", pady=30)
url_input_entry = Entry(main_frame, font=("黑体", 18),width=48)   # 文本输入框组件
url_input_entry.pack(side="left")
url_input_confirm = Button(main_frame, text="确定", font="黑体")    # 确定按钮
url_input_confirm.pack(side="left")
main_frame.pack()
update_range_frame = Frame(root, bd=2)
update_range_frame.pack()
var = BooleanVar()
var.set(False)
update_frame = Frame(root)
# 更新/不更新
Radiobutton(update_frame,text="不更新", variable = var,value=False).pack(side="left")
Radiobutton(update_frame,text="更新", variable = var,value=True).pack(side="left")
update_frame.pack(side="top",fill="x", padx=50)
# 范围
range_frame = Frame(root)
mainloop()
