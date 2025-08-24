# NovelDownloader

### NovelDownloader是一个通过**Chrome浏览器**提取小说资源的提取器，支持下载番茄、起点的小说（起点提取功能发现bug，请勿使用），同时也支持下载封面图片和插图。

**缺点：**

- **需要`vip`或`订阅章节`才能下载完整小说**
- **现仅支持电脑端**
- **暂未实现多线程下载，所以下载速度很慢**
- **使用浏览器现不防验证码**

---

## 简述：

- 拥有账户功能和分组功能
- 可以账户和分组管理、手动管理下载的url的配置
- 满足多种多样的保存需要（`json`，`txt`，`html`）(*html阅读器蓝本由deepseek及豆包提供*)

---

## 使用方法

- 输入1以更新，读取 data\\Record\\UrlCOnfig.json 中的url进行更新（可自选更新的小说）
- 输入2进行下载（可添加参数下载）
- 输入3读取data\\Record\\urls.txt逐行进行下载（可添加参数下载）
- 输入4进行有范围的下载（先输入url，再输入范围）
- 输入5进入设置，支持账户/分组管理

---

## 功能

#### （***小说以我不是戏神为例***）

- **使用Chrome获取小说资源**。
- 账户管理（*默认`Default`*）（*无密码设置*）
- 小说分组管理（*默认`Default`*）
- 可以手动配置参数：
    - 小说分组（*默认`Default`*）
    - 浏览器：
        - 用户数据目录（*默认自带目录*）
        - 延迟（*防止验证码出现*）
    - 保存方式：
        - “`json`”：
            - 名字（*默认小说名字*）
            - 保存路径
            - 图片的保存路径
        - “`txt`”：
            - 名字（*默认小说名字*）
            - 保存路径
            - 分块（*每 N 章一个文件*，默认0，即保存为一个txt文件）
            - 最大文件大小（*每 N MB保存为一个文件，默认-1，即不设置*）
        - “`html`”：
            - 名字（*默认小说名字*）
            - 保存路径
            - 图片嵌入html（"one_file",默认false）
        - “`epub`”：暂无
- 小说下载工具功能列表
    - 下载功能
      | 功能 | 描述 | 参数格式 |
      |------------------|--------------------------|--------------------------------------|
      | **更新小说**     | 更新已存储的小说 | 自选需更新小说（如 `1-3,5,7-9`） |
      | **单本下载**     | 下载单本小说 | `URL [--group] [--update] [--range]`             |
      | **批量下载**     | 批量下载多本小说 | 读取 `urls.txt`<br>（每行格式：`URL [--group] [--update] [--range]`） |
      | **指定章节下载** | 下载特定章节范围 | 输入 `URL [--update]`，再指定章节范围<br>（如 `1-3,5,7-9`）|
      |**设置**          |账户操作，分组操作 |数字选项 |
    - 例子：在单本下载功能中我要下载番茄小说的`我不是戏神`,需要`更新`，也有`范围`（1-3,5,7-9），存到`Default`组，就输入
      `https://fanqienovel.com/page/7276384138653862966 --update=True --range=1-3,5,7-9 --group=Default`
      此更新是显式更新，当UrlConfig.json存此小说参数时可以剔除`--update=True`参数。
      **注意，如果没有此小说json文件或者UrlConfig.json没有存此链接，那么将重新下载**
    - 当你下载时，一些参数会保存在data\Record\UrlConfig.json。参数如下：
        - 账户名
        - 分组
        - 小说链接
        - 小说名字
        - 小说状态
        - 浏览器用户数据目录
        - 保存方式
        - 第一次下载（*时间及时间戳*）
        - 最后一次控制时间（*时间及时间戳*）
          如果你不幸丢失UrlConfig.json或UrlConfig.json损坏并且没有备份（*未实现*），很不幸，你要从头开始下载了（
          *或许你可以自己写一个*）
          **链接及其参数将被保存在`UrlConfig.json`中**

---

## 文件介绍（选读）

- `SettingConfig.json`(*data\\Record\\SettingConfig.json*)
  默认：
  ```json
  {
    "Default": {
        "Group": "Default",
        "User_data_dir": "data\\Record\\Chromedriver\\User Data",
        "Wait_time": [
            1,
            3
        ],
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
        }
    },
    "User": "Default",
    "Users": [
        "Default"
    ],
    "Play_completion_sound": false,
    "Group": "Default",
    "Program_location": "F:\\Administartor1\\Document\\FanQieNovel-Downloader\\NovelDownloader2.0\\src",
    "Unprocessed_download_arguments": []
  }
  ```
  （***注：若需直接修改，请注意参数类型***）
  这里面保存着默认参数，如果下载“陌生”小说，会调用`Default`里面的参数进行下载配置
  **特殊路径**：
  如果下载“陌生”小说时不是此特殊格式而是固定的目录例如`data\\Bookstore\\Default\\Default\\我不是戏神`而下载另一小说时还要自己修改，不方便。
    - `<User>`：被替换成账户名
    - `<Group>`：被替换成组名
    - `<Name>`：被替换成小说名
      只要出现这些字符串，马上会被替换（*区分大小写*）
- `UrlConfig.json`(*data\\Record\\UrlConfig.json*)
  默认：
  ```json
  {
    "Default":
    {
        "Default":{

        }
    }
    }
  ```
  在分组里面保存着各个小说的下载参数，当下载“陌生”小说时会保存着像上面一样的参数，如果再次下载时会调用其参数。
  这是下载了我不是戏神的json
  ```json
  {
    "Default": {
        "Default": {
            "https://fanqienovel.com/page/7276384138653862966": {
                "Name": "我不是戏神",
                "State": "连载中",
                "User_data_dir": "data\\Record\\Chromedriver\\User Data",
                "Save_method": {
                    "json": {
                        "name": "name_default",
                        "dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神",
                        "img_dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神\\Img"
                      },
                    "txt": {
                        "name": "name_default",
                        "dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神",
                        "gap": 0,
                        "max_filesize": -1
                      },
                    "html": {
                        "name": "name_default",
                        "dir": "data\\Bookstore\\Canyang\\Default\\我不是戏神",
                        "gap": 0,
                        "max_filesize": -1,
                        "one_file": true
                      }
                },
                "Wait_time": [
                    1,
                    3
                  ],
                "First_timestamp": 1755858050.630516,
                "First_time": "2025-08-22 18:20:50",
                "Last_control_timestamp": 1755863466.8449166,
                "Last_control_time": "2025-08-22 19:51:06"
              }
        }
    }
    }
    ```

---

- `<Name>.json`:
  这是保存小说信息的json（*`<Name>`替换成小说名*），如果移动到另一目录你需要修改UrlConfig.json对应的目录信息，否则无法更新以至于重新下载
  格式（不完整）:
  ```json
  {
    "version": "1.0.0",
    "info": {
        "name": "我不是戏神",
        "author": "三九音域",
        "author_desc": "",
        "label": "",
        "count_word": "",
        "last_update": "",
        "abstract": "",
        "book_cover_data": "",
        "url": ""
    },
    "chapters": {
        "第1章 戏鬼回家": {
            "url": "https://fanqienovel.com/reader/7276663560427471412",
            "update": "",
            "count_word": "",
            "content": "",
            "integrity": true,
            "img_item": {}
        }
    }
  }
  ```
  `book_cover_data`和`img_item`的值存放着base64格式的图片数据（*`data:image/png;base64,`+base64图片*
  ）此json大小随小说图片的增加呈爆炸级增长

- `template.html`(*data\\Record\\template.html*)
  这是html阅读器的蓝本，里面的`<&?NovelData!&>`会被替换成小说的json，此蓝本由deepseek及豆包提供。拥有书签、设置功能
  （*调了三天了，作者又不会网页端语言，所以有bug。书签功能可以去掉，没什么用*）
  **如果小说的json过大时此html加载速度会很慢**。（*144MB的html打开时加载约1分钟，手机端约2-3分钟*）

---

## 免责声明

**此程序旨在用于与Python网络爬虫和网页处理技术相关的教育和研究目的。不应将其用于任何非法活动或侵犯他人权利的行为。用户对使用此程序引发的任何法律责任和风险负有责任，作者不对因使用程序而导致的任何损失或损害承担责任。
**

**在使用此程序之前，请确保遵守相关法律法规以及网站的使用政策，并在有任何疑问或担忧时咨询法律顾问。**

---

## 关于反病毒软件误报的说明

**本程序使用了 `Nuitka` 工具进行封装。由于 Nuitka 的`压缩和封装方式与一些木马较为相似`
，部分反病毒软件在扫描时可能会将其误判为威胁。这种误报并非表示程序本身有问题，而是因为反病毒软件通过特征匹配判断出风险。实际上，这种情况在
`使用 Nuitka 打包的 Python 程序中并不少见`，很多恶意程序也使用了同样的工具进行分发，导致反病毒软件难以区分。**

### 解决方案：

- 如果您希望避免误报，最稳妥的方式是：自行安装 `Python 环境`，从官方仓库克隆源代码后直接运行。

- 如果确实需要使用预编译版本，并且您信任本程序及开发者，`也可以将程序添加到反病毒软件的白名单中`。

- 本着`安全第一`的原则，如果确实对本程序及开发者不信任，请`使用其他同类工具替代`。

---

## 作者：Canyang008

---

## 想法：

- 想将此项目`做成GUI`，本项目更适合做成GUI模式，但是关于这些知识还没学会（*`tkinter`过于简陋*）
- 提示登录用户状态
- 设置功能更加全面
- 做出html分块和最大文件保存功能
- 计划做出支持以epub格式保存
- 备份功能
  **……**

---

## 欢迎提出新的点子~（QQ：765857967）