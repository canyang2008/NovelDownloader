# 说明

## 这是介绍一些功能的README

### JSON介绍

**为了让用户更灵活的配置，下面将讲解JSON的作用  
注意:值的类型一定要正确**  
`VERSION | Version | version`: 最后一次文件结构更新

- #### `manage.json`: 管理所有用户的配置

  演示：

  ```json
  {
    "VERSION": "1.1.0",
    "README": "",
    "USER": "Default",
    "USERS": {
      "Default": {
        "User_config_path": "data/Local/Default/UserConfig.json",
        "User_data_dir": "data/Local/Default/User Data",
        "Base_dir": "data/Local/Default/json"
      }
    }
  }
  
  ```

  **特殊目录介绍**

  - `<User>`: 替换为当前用户名
  - `<Group>`: 替换为当前分组名
  - `<T:''>`: 替换为单引号内通过时间戳转换的时间格式

  **UserConfig.json参数介绍**

  - `USER` -> `str`: 当前用户
  - `USERS` -> `dict`: 所有用户的配置
    - `User_config_path` -> `str`: 当前用户下的`UserConfig.json`的路径
    - `User_data_dir` -> `dict`: 当前用户下的浏览器用户数据目录
    - `Base_dir` -> `str`: 当前用户下的最基本的保存小说的JSON的目录，目录一定要包含`mems.json`

- #### `UserConfig.json`: 当前用户的所有配置

  演示：

  ```json
  {
    "Version": "1.1.1",
    "User_name": "Default",
    "Group": "Default",
    "README": "",
    "Play_completion_sound": false,
    "Get_mode": 0,
    "Threads_num": 1,
    "Browser": {
        "State": {
            "Fanqie": 0,
            "Qidian": 0,
            "Bqg128": 0
        },
        "Timeout": 10,
        "Max_retry": 3,
        "Interval": 2,
        "Delay": [
            1,
            3.0
        ],
        "Port": 9445,
        "Headless": false
    },
    "Api": {
        "Fanqie": {
            "Option": "oiapi",
            "oiapi": {
                "Max_retry": 3,
                "Timeout": 10,
                "Interval": 2,
                "Delay": [
                    1,
                    3
                ],
                "Key": ""
            }
        },
        "Qidian": {},
        "Biquge": {}
    },
    "Requests": {
        "Fanqie": {
            "Max_retry": 3,
            "Timeout": 10,
            "Interval": 2,
            "Delay": [
                1,
                3
            ],
            "Cookie": ""
        },
        "Qidian": {
            "Max_retry": 3,
            "Timeout": 10,
            "Interval": 2,
            "Delay": [
                1,
                3
            ],
            "Cookie": ""
        },
        "Biquge": {
            "Max_retry": 3,
            "Timeout": 10,
            "Interval": 2,
            "Delay": [
                1,
                3
            ],
            "Cookie": ""
        }
    },
    "Save_method": {
        "json": {
            "name": "name_default",
            "dir": "data\\Bookstore\\<User>\\<Group>\\<Name>",
            "img_dir": "data\\Bookstore\\<User>\\<Group>\\<Name>\\Img"
        },
        "txt": {
            "name": "name_default",
            "dir": "data\\Bookstore\\<User>\\<Group>\\<Name>",
            "gap": 0,
            "max_filesize": -1
        },
        "html": {
            "name": "name_default",
            "dir": "data\\Bookstore\\<User>\\<Group>\\<Name>",
            "one_file": true
        }
    },
    "Unprocess": [],
    "Backup": {
        "Auto": false,
        "Auto_save_method": "T:86400",
        "Dir": "C:\\\\",
        "Name": "Novel_backup <User><T:'%Y-%m-%d'>.zip",
        "Last_time": -1,
        "Pop_up_folder": false
    }
  }
  ```

  **参数介绍**

  - `Play_completion_sound` -> `bool`: 下载完成后是否播放提示音
  - `Get_mode` -> `int`: 获取模式
    - 0: Chrome浏览器模式
    - 1: API模式（仅番茄）
  - `Threads_num`: 线程数（未实现多线程）
  - `Browser` -> `dict`: Chrome配置
    - `State` -> `dict`: 各网站的登陆状态（未应用）
      - `Fanqie` -> `int`:
        - -1: 未登录
        - 0: 已登录但无VIP
        - 1: 有VIP
      - `Qidian` -> `int`:
        - -1: 未登录
        - 1: 已登录
      - `Bqg128` -> `int`:
        - -1: 未登录
        - 1: 已登录
    - `Timeout` -> `int`: 获取html超时时间（未应用）
    - `Max_retry` -> `int`: 最大重试次数（未应用）
    - `Interval` -> `int`: 重试的时间间隔（未应用）
    - `Delay` -> `list[float,float]`: 延迟，上下限
    - `Port` -> `int`: 浏览器端口号
    - `Headless` -> `bool`: 浏览器是否以无头模式启动
  - `Api` -> `dict`: API配置
    - `Fanqie` -> `dict`: 番茄配置
      - `Option` -> `str`: 选择哪种配置
        - `oiapi` -> `dict`: oiapi配置
          - `Max_retry` -> `int`:  最大重试次数（未应用）
          - `Interval` -> `int`: 重试的时间间隔（未应用）
          - `Delay` -> `list[float,float]`: 延迟，分别为上下限
          - `Key` -> `str`: API的KEY
    - `Qidian` -> `dict`: 起点配置
    - `Biquge` -> `dict`: 笔趣阁配置
  - `Requests` -> `dict`: requests配置（未应用）
  - `Save_method` -> `dict`: 保存方式
    - `json` -> `dict`:保存json及其配置
      - `enable` -> `bool`: 是否以该格式保存
      - `name` -> `str`: 保存的文件名，默认`name_default`，即当前小说名字
      - `dir` -> `str`: 保存目录
      - `img_dir` -> `str`: 图片保存目录
    - `txt` -> `dict`:保存txt及其配置
      - `enable` -> `bool`: 是否以该格式保存
      - `name` -> `str`: 保存的文件名，默认`name_default`，即当前小说名字
      - `dir` -> `str`: 保存目录
      - `gap` -> `int`: 分块保存，默认为0，即但文件保存
      - `max_filesize` -> `int`: 以文本大小切割，当大于 N KB时切割保存，单位：KB
    - `html` -> `dict`:保存txt及其配置
      - `enable` -> `bool`: 是否以该格式保存
      - `name` -> `str`: 保存的文件名，默认`name_default`，即当前小说名字
      - `dir` -> `str`: 保存目录
      - `one_file` -> `bool`: 是否把图片数据嵌入至html中以保存为一个文件
  - `Unprocess` -> `list`: 未处理的url，当下载中断时通过它继续下载（未应用）
  - `Backup` -> `dict`: 备份配置，备份以无压缩的ZIP保存
    - `Auto` -> `bool`: 是否自动保存
    - `Auto_save_method` -> `str`: 自动保存方式
      - T开头:通过时间保存。以`T:86400`为例，每隔86400秒自动保存
      - ……
    - `Dir` -> `str`: 备份保存目录
    - `Name` -> `str`: ZIP名字
    - `Last_time` -> `float`: 上次备份的时间戳
    - `Pop_up_folder` -> `bool`: 当选择文件夹时是否弹出文件夹选择框
  
- `mems.json`: 管理分组及其小说，是更新功能的标配
  演示：

  ```json
  {
    "Version": "1.1.0",
    "Default": {"https://fanqienovel.com/page/7276384138653862966": "我不是戏神"
    }
  }
  ```

  **mems.json参数介绍**

  - `Default` -> `dict`: 分组名称及其内的小说成员
    - `https://fanqienovel.com/page/7276384138653862966` -> `str`: 小说目录页链接和小说名

- `<novel>.json`: 小说的JSON数据
  演示：

  ```json
  {
    "version": "1.1.0",
    "info": {
        "name": "我不是戏神",
        "author": "三九音域",
        "author_desc": "用心写出不一样的故事",
        "label": "连载中 都市高武 都市 穿越",
        "count_word": "3246103字",
        "last_update": "最近更新：第1558章 寂灭现身 2025-10-01 19:00:24",
        "abstract": "赤色流星划过天际后，人类文明陷入停滞。\n从那天起，人们再也无法制造一枚火箭，一颗核弹，一架飞机，一台汽车……近代科学堆砌而成的文明金字塔轰然坍塌，而灾难，远不止此。\n灰色的世界随着赤色流星降临，像是镜面后的鬼魅倒影，将文明世界一点点拖入无序的深渊。\n在这个时代，人命渺如尘埃；\n在这个时代，人类灿若星辰。\n大厦将倾，有人见一戏子屹立文明废墟之上，红帔似血，时笑时哭，\n时代的帘幕在他身后缓缓打开，他张开双臂，对着累累众生轻声低语——\n“好戏……开场。”",
        "book_cover_data": "data:image/png;base64,",
        "url": "https://fanqienovel.com/page/7276384138653862966"
    },
    "chapters": {
        "第1章 戏鬼回家": {
            "url": "https://fanqienovel.com/reader/7276663560427471412",
            "update": "更新时间：2023-09-28",
            "count_word": "本章字数：2057字",
            "content": "",
            "integrity": true,
            "img_item": {
              "(1) [desc]":"data:image/png;base64," 
              }
        }
     },
    "config": {
        "Version": "1.1.0",
        "Name": "我不是戏神",
        "Group": "Default",
        "Max_retry": 3,
        "Timeout": 10,
        "Interval": 2,
        "Delay": [
            1,
            3
        ],
        "Save_method": {
            "json": {
                "name": "name_default",
                "dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神",
                "img_dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神\\Img"
            },
            "txt": {
                "name": "name_default",
                "dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神",
                "gap": 2,
                "max_filesize": 4096
            },
            "html": {
                "name": "name_default",
                "dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神",
                "gap": 0,
                "max_filesize": -1,
                "one_file": true
            }
        },
        "First_time_stamp": 1759390668.270462,
        "Last_control_timestamp": 1759390668.3173263
      }
    }
  ```

  **`<novel>.json`参数介绍**

  - `version`: 小说完整结构 | 值的类型最后一次更新版本
  - `info` -> `dict`: 小说信息
    - `name` -> `str`: 小说名称
    - `author` -> `str`: 作者
    - `author_desc` -> `str`: 作者描述
    - `label` -> `str`: 标签
    - `count_word` -> `str`: 小说总字数
    - `last_update` -> `str`: 最后更新信息，受下载时间影响
    - `abstract` -> `str`: 作品简介
    - `book_cover_data` -> `str`: 封面图片的base64数据（HTML）
    - `url` -> `str`: 小说目录页链接
  - `chapters` -> `dict`: 章节信息
    - `第1章 戏鬼回家` -> `dict`: 某一章章节信息
    - `url` -> `str`: 小说章节页的链接
    - `update` -> `str`: 更新时间
    - `count_word` -> `str`: 本章字数
    - `content` -> `str`: 章节文本内容
    - `integrity` -> `str`: 小说能获取到的文本内容是否完整
    - `img_item` -> `dict`: 章节插图信息
      - `(1) [desc]` -> `str`: 图片描述，保存的是插图base64数据（HTML）
  - `config` -> `dict`: 保存的是下载该小说时的保存的配置，下次下载时应用其配置
    - `Version` -> `str`: 配置结构最后一次更新的版本
    - `Name` -> 小说名称:
    - `Group` -> 小说的组:
    - `Max_retry` -> `int`:  最大重试次数（未应用）
    - `Interval` -> `int`: 重试的时间间隔（未应用）
    - `Delay` -> `list[float,float]`: 延迟，分别为上下限
    - `Save_method` -> `dict`: 保存方式
      - `json` -> `dict`:保存json及其配置
      - `enable` -> `bool`: 是否以该格式保存
        - `name` -> `str`: 保存的文件名，默认`name_default`，即当前小说名字
        - `dir` -> `str`: 保存目录
        - `img_dir` -> `str`: 图片保存目录
      - `txt` -> `dict`:保存txt及其配置
      - `enable` -> `bool`: 是否以该格式保存
        - `name` -> `str`: 保存的文件名，默认`name_default`，即当前小说名字
        - `dir` -> `str`: 保存目录
        - `gap` -> `int`: 分块保存，默认为0，即但文件保存
        - `max_filesize` -> `int`: 以文本大小切割，当大于 N KB时切割保存，单位：KB
      - `html` -> `dict`:保存txt及其配置
      - `enable` -> `bool`: 是否以该格式保存
        - `name` -> `str`: 保存的文件名，默认`name_default`，即当前小说名字
        - `dir` -> `str`: 保存目录
        - `one_file` -> `bool`: 是否把图片数据嵌入至html中以保存为一个文件
    - `First_time_stamp` -> `int`: 首次下载时间戳（未应用）
    - `Last_control_timestamp` -> `int`: 最后一次控制的时间戳（未应用）
