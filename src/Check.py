import json
import os

from colorama import Fore


class Check:
    def __init__(self): pass


def init():
    os.makedirs("data/Local", exist_ok=True)

    init_manage = {
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
    with open(f"data/Local/manage.json", "w", encoding="utf-8") as f:
        json.dump(init_manage, f, ensure_ascii=False, indent=4)

    init_userconfig = {
        "Version": "1.1.0",
        "User_name": "Default",
        "Group": "Default",
        "README": "",
        "Play_completion_sound": False,
        "Get_mode": 0,
        "Browser": {
            "State": {
                "Fanqie": -1,
                "Qidian": 0,
                "Bqg128": 0
            },
            "Timeout": 10,
            "Max_retry": 3,
            "Interval": 2,
            "Delay": [
                1,
                1.5
            ],
            "Port": 9445,
            "Headless": False
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
                "one_file": True
            }
        },
        "Unprocess": []
    }

    os.makedirs(f"data/Local/Default", exist_ok=True)
    with open(f"data/Local/Default/UserConfig.json", "w", encoding="utf-8") as f:
        json.dump(init_userconfig, f, ensure_ascii=False, indent=4)
    os.makedirs(f"data/Local/Default/User Data", exist_ok=True)
    os.makedirs(f"data/Local/Default/json", exist_ok=True)
    init_mems = {
        "Version": "1.1.0",
        "Default": {
        }
    }
    with open(f"data/Local/Default/json/mems.json", "w", encoding="utf-8") as f:
        json.dump(init_mems, f, ensure_ascii=False, indent=4)

    template = """<!DOCTYPE html>
<html lang="zh-CN">

<head>
    <meta charset="UTF-8">
    <meta content="width=device-width, initial-scale=1.0" name="viewport">
    <title>小说阅读器</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
        }

        :root {
            --primary: #8a2be2;
            --primary-dark: #6a1cb9;
            --bg-dark: #121212;
            --bg-content: #1e1e1e;
            --text-primary: #e0e0e0;
            --text-secondary: #b0b0b0;
            --border: #333;
            --accent: #ff6b6b;
            --chapter-hover: #2d2d2d;
            --light-bg: #f5f5f5;
            --light-text: #333;
            --light-border: #ddd;
            --font-size: 1.1rem;
            --line-height: 1.8;
            --page-width: 900px;
            --complete: #4caf50;
            --incomplete: #ff9800;
            --bg-paper: #f8f5e6;
            --bg-sepia: #f4ecd8;
            --bg-green: #eaf4ea;
            --paragraph-spacing: 1.5;
        }

        body {
            background-color: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            min-height: 100vh;
            transition: all 0.3s ease;
            font-size: var(--font-size);
            font-family: var(--font-family, 'Segoe UI', 'Microsoft YaHei', sans-serif);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 0;
            margin: 0;
        }

        body.light-theme {
            background-color: var(--light-bg);
            color: var(--light-text);
        }

        body.paper-theme {
            background-color: var(--bg-paper);
            color: #5d4037;
        }

        body.sepia-theme {
            background-color: var(--bg-sepia);
            color: #594433;
        }

        body.green-theme {
            background-color: var(--bg-green);
            color: #2e7d32;
        }

        body.night-theme {
            background-color: #0a0a0a;
            color: #c8c8c8;
        }

        .sidebar {
            width: 300px;
            background-color: var(--bg-content);
            border-right: 1px solid var(--border);
            height: 100%;
            position: fixed;
            overflow-y: auto;
            padding: 20px;
            transition: transform 0.3s ease;
            z-index: 100;
            transform: translateX(0);
            left: 0;
            top: 0;
            box-shadow: 3px 0 10px rgba(0, 0, 0, 0.3);
            bottom: 0; /* 添加底部定位 */
            display: flex; /* 弹性布局 */
            flex-direction: column; /* 垂直方向排列 */
        }

        .sidebar.hidden {
            transform: translateX(-100%);
        }

        .light-theme .sidebar,
        .paper-theme .sidebar,
        .sepia-theme .sidebar,
        .green-theme .sidebar {
            background-color: white;
            border-right: 1px solid var(--light-border);
        }

        .night-theme .sidebar {
            background-color: #1a1a1a;
            border-right: 1px solid #333;
        }

        .book-cover {
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
            margin-bottom: 20px;
            aspect-ratio: 3/4;
            object-fit: cover;
        }

        .book-title {
            font-size: 1.8rem;
            margin-bottom: 10px;
            color: white;
            font-weight: 700;
        }

        .light-theme .book-title,
        .paper-theme .book-title,
        .sepia-theme .book-title,
        .green-theme .book-title {
            color: var(--light-text);
        }

        .night-theme .book-title {
            color: #e0e0e0;
        }

        .book-title a {
            color: inherit;
            text-decoration: none;
            transition: color 0.3s;
        }

        .book-title a:hover {
            color: var(--accent);
        }

        .book-meta {
            color: var(--text-secondary);
            margin-bottom: 15px;
            font-size: 0.95rem;
        }

        .light-theme .book-meta,
        .paper-theme .book-meta,
        .sepia-theme .book-meta,
        .green-theme .book-meta {
            color: #666;
        }

        .night-theme .book-meta {
            color: #aaa;
        }

        .book-meta span {
            display: block;
            margin-bottom: 5px;
        }

        .book-meta .author {
            color: var(--accent);
            font-weight: 500;
        }

        .light-theme .book-meta .author,
        .paper-theme .book-meta .author,
        .sepia-theme .book-meta .author,
        .green-theme .book-meta .author {
            color: #d35400;
        }

        .book-meta .status {
            background: linear-gradient(45deg, var(--primary), var(--accent));
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            display: inline-block;
            margin-top: 5px;
            color: white;
        }

        .abstract {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            font-size: 0.95rem;
            line-height: 1.7;
            border-left: 3px solid var(--primary);
        }

        .light-theme .abstract,
        .paper-theme .abstract,
        .sepia-theme .abstract,
        .green-theme .abstract {
            background: rgba(0, 0, 0, 0.05);
            border-left: 3px solid var(--primary);
        }

        .night-theme .abstract {
            background: rgba(255, 255, 255, 0.03);
        }

        .chapter-list {
            margin-top: 20px;
        }

        .chapter-list h3 {
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .light-theme .chapter-list h3,
        .paper-theme .chapter-list h3,
        .sepia-theme .chapter-list h3,
        .green-theme .chapter-list h3 {
            border-bottom: 1px solid var(--light-border);
        }

        .chapters {
            max-height: 300px;
            overflow-y: auto;
            padding-right: 5px;
            flex: 1; /* 填充剩余空间 */
            min-height: 0; /* 允许内容溢出时滚动 */
        }

        .chapter-item {
            padding: 12px 15px;
            border-radius: 6px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: relative;
        }

        .chapter-item:hover {
            background-color: var(--chapter-hover);
        }

        .light-theme .chapter-item:hover,
        .paper-theme .chapter-item:hover,
        .sepia-theme .chapter-item:hover,
        .green-theme .chapter-item:hover {
            background-color: #f0f0f0;
        }

        .night-theme .chapter-item:hover {
            background-color: #2a2a2a;
        }

        .chapter-item.active {
            background: linear-gradient(90deg, var(--primary), transparent);
            border-left: 3px solid var(--accent);
        }

        .chapter-info {
            font-size: 0.8rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .chapter-status {
            font-size: 0.9em;
        }

        .chapter-status.complete {
            color: var(--complete);
        }

        .chapter-status.incomplete {
            color: var(--incomplete);
        }

        .chapter-link {
            color: #aaa;
            transition: color 0.3s;
        }

        .chapter-link:hover {
            color: var(--accent);
        }

        .main-content {
            max-width: var(--page-width);
            width: 100%;
            margin: 0 auto;
            padding: 30px;
            transition: max-width 0.3s ease;
            position: relative;
            background-color: rgba(30, 30, 30, 0.8);
            border-radius: 8px;
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.3);
            margin-top: 30px;
            margin-bottom: 30px;
        }

        .sidebar.hidden ~ .main-content {
            margin-left: auto;
            margin-right: auto;
        }

        .light-theme .main-content,
        .paper-theme .main-content,
        .sepia-theme .main-content,
        .green-theme .main-content {
            background-color: rgba(255, 255, 255, 0.8);
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05);
            border-radius: 8px;
        }

        .night-theme .main-content {
            background-color: rgba(26, 26, 26, 0.8);
            box-shadow: 0 2px 15px rgba(0, 0, 0, 0.3);
            border-radius: 8px;
        }

        .chapter-header {
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
        }

        .light-theme .chapter-header,
        .paper-theme .chapter-header,
        .sepia-theme .chapter-header,
        .green-theme .chapter-header {
            border-bottom: 1px solid var(--light-border);
        }

        .chapter-title-container {
            display: flex;
            align-items: center;
            gap: 15px;
            flex-wrap: wrap;
        }

        .chapter-title {
            font-size: 1.8rem;
            color: white;
        }

        .light-theme .chapter-title,
        .paper-theme .chapter-title,
        .sepia-theme .chapter-title,
        .green-theme .chapter-title {
            color: var(--light-text);
        }

        .chapter-meta {
            color: var(--text-secondary);
            font-size: 0.95rem;
            display: flex;
            gap: 15px;
        }

        .chapter-status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }

        .chapter-status-indicator.complete {
            background-color: rgba(76, 175, 80, 0.15);
            color: var(--complete);
        }

        .chapter-status-indicator.incomplete {
            background-color: rgba(255, 152, 0, 0.15);
            color: var(--incomplete);
        }

        .chapter-content {
            line-height: var(--line-height);
            padding-bottom: 50px;
            text-align: justify;
            font-size: var(--font-size);
            font-family: var(--font-family);
        }

        .chapter-content div {
            margin-bottom: calc(var(--paragraph-spacing) * 1em);
        }

        .chapter-content p {
            margin-bottom: 0.8em;
        }

        .chapter-content img {
            max-width: 100%;
            display: block;
            margin: 15px auto;
            border-radius: 5px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
            background-color: #f5f5f5;
            min-height: 200px;
            max-height: 40vh; /* 限制最大高度为视口高度的60% */
             width: auto; /* 保持宽高比 */
             object-fit: contain; /* 保持比例完整显示图片 */
        }

        .reading-progress {
            position: fixed;
            top: 0;
            left: 0;
            height: 3px;
            background-color: #8a2be2;
            z-index: 9999;
            transition: width 0.2s ease;
        }

        .navigation {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
        }

        .nav-btn {
            background-color: var(--primary);
            color: white;
            border: none;
            padding: 10px 25px;
            border-radius: 30px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav-btn:hover {
            background-color: var(--primary-dark);
            transform: translateY(-2px);
            box-shadow: 0 4px 10px rgba(138, 43, 226, 0.3);
        }

        .nav-btn:disabled {
            background-color: #555;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }

        .bookmark {
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: var(--primary);
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 200;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            transition: all 0.3s;
        }

        .bookmark:hover {
            transform: scale(1.1);
        }

        .toggle-sidebar {
            position: fixed;
            top: 20px;
            left: 20px;
            background-color: var(--primary);
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 200;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            display: flex;
        }

        .settings-btn {
            position: fixed;
            top: 85px;
            right: 20px;
            background-color: var(--primary);
            color: white;
            border: none;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 200;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            transition: all 0.3s;
        }

        .settings-btn:hover {
            transform: scale(1.1);
        }

        .footer {
            text-align: center;
            padding: 20px;
            color: var(--text-secondary);
            font-size: 0.9rem;
            margin-top: 30px;
            border-top: 1px solid var(--border);
        }

        .settings-panel {
            position: fixed;
            top: 150px;
            right: 20px;
            background-color: var(--bg-content);
            border-radius: 10px;
            padding: 20px;
            width: 300px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            z-index: 199;
            transform: translateX(110%);
            transition: transform 0.3s ease;
            max-height: calc(100vh - 180px);
            overflow-y: auto;
        }

        .settings-panel.open {
            transform: translateX(0);
        }

        .light-theme .settings-panel {
            background-color: white;
            border: 1px solid var(--light-border);
        }

        .settings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
        }

        .close-settings {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
            transition: color 0.3s;
        }

        .close-settings:hover {
            color: var(--accent);
        }

        .settings-group {
            margin-bottom: 20px;
        }

        .settings-group h4 {
            margin-bottom: 10px;
            font-size: 1rem;
        }

        .font-size-controls {
            display: flex;
            gap: 10px;
        }

        .font-size-btn {
            flex: 1;
            padding: 8px;
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }

        .font-size-btn:hover, .font-size-btn.active {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .font-family-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .font-family-btn {
            flex: 1;
            min-width: 100px;
            padding: 8px;
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }

        .font-family-btn.serif {
            font-family: Georgia, 'Times New Roman', serif;
        }

        .font-family-btn.sans-serif {
            font-family: 'Segoe UI', Arial, sans-serif;
        }

        .font-family-btn.mono {
            font-family: 'Courier New', monospace;
        }

        .font-family-btn.zh {
            font-family: 'Microsoft YaHei', 'SimSun', sans-serif;
        }

        .font-family-btn:hover, .font-family-btn.active {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .theme-controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .theme-btn {
            flex: 1;
            min-width: 80px;
            padding: 8px;
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }

        .theme-btn:hover, .theme-btn.active {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .line-height-controls {
            display: flex;
            gap: 10px;
        }

        .line-height-btn {
            flex: 1;
            padding: 8px;
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }

        .line-height-btn:hover, .line-height-btn.active {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .paragraph-spacing-controls {
            display: flex;
            gap: 10px;
        }

        .paragraph-spacing-btn {
            flex: 1;
            padding: 8px;
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }

        .paragraph-spacing-btn:hover, .paragraph-spacing-btn.active {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .page-width-controls {
            display: flex;
            gap: 10px;
        }

        .page-width-btn {
            flex: 1;
            padding: 8px;
            background-color: rgba(255, 255, 255, 0.1);
            border: 1px solid var(--border);
            border-radius: 5px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
        }

        .page-width-btn:hover, .page-width-btn.active {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        .setting-switch {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 50px;
            height: 24px;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #555;
            transition: .4s;
            border-radius: 24px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: var(--primary);
        }

        input:checked + .slider:before {
            transform: translateX(26px);
        }

        .progress-display {
            text-align: center;
            margin-top: 10px;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .theme-preview {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
            vertical-align: middle;
        }

        .theme-dark .theme-preview {
            background: #121212;
        }

        .theme-light .theme-preview {
            background: #f5f5f5;
        }

        .theme-paper .theme-preview {
            background: #f8f5e6;
        }

        .theme-sepia .theme-preview {
            background: #f4ecd8;
        }

        .theme-green .theme-preview {
            background: #eaf4ea;
        }

        .theme-night .theme-preview {
            background: #0a0a0a;
        }

        @media (max-width: 768px) {
            .chapter-content img {
                max-height: 50vh; /* 在移动设备上使用更小的高度 */
            }
            .sidebar {
                width: 260px;
            }

            .main-content {
                padding: 15px;
                margin-left: 0 !important;
                margin-top: 70px;
            }

            .chapter-title {
                font-size: 1.5rem;
            }

            .nav-btn {
                padding: 8px 15px;
                font-size: 0.9rem;
            }

            .settings-panel {
                width: 90%;
                max-width: 300px;
                top: 100px;
                right: 5%;
            }

            .toggle-sidebar, .settings-btn, .bookmark {
                width: 40px;
                height: 40px;
                font-size: 0.9rem;
            }

            .settings-btn {
                top: 70px;
            }
        }
    </style>
</head>

<body>
<div class="reading-progress" id="readingProgress"></div>

<div class="sidebar" id="sidebar">
</div>

<div class="main-content">
    <div class="chapter-header">
        <div class="chapter-title-container">
            <h2 class="chapter-title" id="chapterTitle"></h2>
            <div class="chapter-status-indicator complete" id="chapterStatus">
                <i class="fas fa-check-circle"></i>

            </div>
        </div>
        <div class="chapter-meta">
            <span><i class="far fa-calendar"></i> </span>
            <span><i class="fas fa-file-word"></i> </span>
        </div>
    </div>

    <div class="chapter-content" id="chapterContent">
    </div>

    <div class="navigation">
        <button class="nav-btn" disabled id="prevBtn">
            <i class="fas fa-arrow-left"></i> 上一章
        </button>
        <button class="nav-btn" id="nextBtn">
            下一章 <i class="fas fa-arrow-right"></i>
        </button>
    </div>

    <div class="footer">
        <p>© 2025 <span id="bottomAuthor"></span> 版权所有 | 本阅读器仅供个人阅读使用</p>
    </div>
</div>

<button class="bookmark" id="bookmarkBtn">
    <i class="fas fa-bookmark"></i>
</button>

<button class="settings-btn" id="settingsBtn">
    <i class="fas fa-cog"></i>
</button>

<div class="settings-panel" id="settingsPanel">
    <div class="settings-header">
        <h3>阅读设置</h3>
        <button class="close-settings" id="closeSettings">&times;</button>
    </div>

    <div class="settings-group">
        <h4>字体大小</h4>
        <div class="font-size-controls">
            <div class="font-size-btn" data-size="0.9">小</div>
            <div class="font-size-btn active" data-size="1.1">中</div>
            <div class="font-size-btn" data-size="1.3">大</div>
            <div class="font-size-btn" data-size="1.5">特大</div>
        </div>
    </div>

    <div class="settings-group">
        <h4>字体</h4>
        <div class="font-family-controls">
            <div class="font-family-btn sans-serif active" data-family="'Segoe UI', Arial, sans-serif">无衬线</div>
            <div class="font-family-btn serif" data-family="Georgia, 'Times New Roman', serif">衬线</div>
            <div class="font-family-btn mono" data-family="'Courier New', monospace">等宽</div>
            <div class="font-family-btn zh" data-family="'Microsoft YaHei', 'SimSun', sans-serif">中文</div>
        </div>
    </div>

    <div class="settings-group">
        <h4>主题</h4>
        <div class="theme-controls">
            <div class="theme-btn theme-dark active" data-theme="dark"><span class="theme-preview"></span>深色</div>
            <div class="theme-btn theme-light" data-theme="light"><span class="theme-preview"></span>浅色</div>
            <div class="theme-btn theme-paper" data-theme="paper"><span class="theme-preview"></span>纸张</div>
            <div class="theme-btn theme-sepia" data-theme="sepia"><span class="theme-preview"></span>复古</div>
            <div class="theme-btn theme-green" data-theme="green"><span class="theme-preview"></span>护眼</div>
            <div class="theme-btn theme-night" data-theme="night"><span class="theme-preview"></span>夜间</div>
        </div>
    </div>

    <div class="settings-group">
        <h4>行高</h4>
        <div class="line-height-controls">
            <div class="line-height-btn" data-height="1.6">紧凑</div>
            <div class="line-height-btn active" data-height="1.8">适中</div>
            <div class="line-height-btn" data-height="2.0">宽松</div>
            <div class="line-height-btn" data-height="2.2">极宽松</div>
        </div>
    </div>

    <div class="settings-group">
        <h4>段落间距</h4>
        <div class="paragraph-spacing-controls">
            <div class="paragraph-spacing-btn" data-spacing="1.0">紧凑</div>
            <div class="paragraph-spacing-btn active" data-spacing="1.5">适中</div>
            <div class="paragraph-spacing-btn" data-spacing="2.0">宽松</div>
        </div>
    </div>

    <div class="settings-group">
        <h4>页面宽度</h4>
        <div class="page-width-controls">
            <div class="page-width-btn" data-width="600px">窄</div>
            <div class="page-width-btn active" data-width="900px">中</div>
            <div class="page-width-btn" data-width="1200px">宽</div>
            <div class="page-width-btn" data-width="100%">全屏</div>
        </div>
    </div>

    <div class="settings-group">
        <h4>阅读选项</h4>
        <div class="setting-switch">
            <span>阅读进度条</span>
            <label class="switch">
                <input checked id="progressBarSwitch" type="checkbox">
                <span class="slider"></span>
            </label>
        </div>
        <div class="setting-switch">
            <span>章节末尾提示</span>
            <label class="switch">
                <input checked id="chapterEndHint" type="checkbox">
                <span class="slider"></span>
            </label>
        </div>
        <div class="setting-switch">
            <span>双击全屏阅读</span>
            <label class="switch">
                <input id="doubleClickFullscreen" type="checkbox">
                <span class="slider"></span>
            </label>
        </div>
    </div>

    <div class="settings-group">
        <div class="progress-display" id="progressDisplay">
            当前阅读进度: 0%
        </div>
    </div>
</div>

<button class="toggle-sidebar" id="toggleSidebar">
    <i class="fas fa-bars"></i>
</button>

<script>
    // 小说数据
    const novelData = <&?NovelData!&>;
    // 修改标题
    document.title = `${novelData['info']['name']} - 小说阅读器`

    // 图片损坏时的占位图片（SVG格式）
    const brokenImageSVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <rect width="100" height="100" fill="#f0f0f0"/>
        <line x1="10" y1="10" x2="90" y2="90" stroke="#ccc" stroke-width="5"/>
        <line x1="10" y1="90" x2="90" y2="10" stroke="#ccc" stroke-width="5"/>
        <text x="50" y="50" text-anchor="middle" dominant-baseline="middle" font-size="12" fill="#666">图片已损毁</text>
    </svg>`;
    const brokenImageBase64 = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(brokenImageSVG)));
            // 初始化阅读器
    document.addEventListener('DOMContentLoaded', () => {
        // 获取页面元素
        const sidebar = document.getElementById('sidebar');
        const chapterListContainer = document.createElement('div');
        chapterListContainer.className = 'chapters';
        chapterListContainer.id = 'chapterList';

        const chapterTitle = document.getElementById('chapterTitle');
        const chapterContent = document.getElementById('chapterContent');
        const chapterStatus = document.getElementById('chapterStatus');
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');
        const bookmarkBtn = document.getElementById('bookmarkBtn');
        const toggleSidebar = document.getElementById('toggleSidebar');
        const settingsBtn = document.getElementById('settingsBtn');
        const settingsPanel = document.getElementById('settingsPanel');
        const closeSettings = document.getElementById('closeSettings');
        const readingProgress = document.getElementById('readingProgress');
        const progressDisplay = document.getElementById('progressDisplay');
        const progressBarSwitch = document.getElementById('progressBarSwitch');
        const autoNextChapter = document.getElementById('autoNextChapter');
        const chapterEndHint = document.getElementById('chapterEndHint');
        const doubleClickFullscreen = document.getElementById('doubleClickFullscreen');
        const bottomAopyrightAuthor = document.getElementById('bottomAuthor')
        // 初始化变量
        let currentChapter = 0;
        const chapterKeys = Object.keys(novelData.chapters);
        const namespace = "novelReader_" + novelData.info.name.replace(/\s+/g, '_');

        // 动态加载侧边栏内容
        function loadSidebarContent() {
            const coverBase64 = novelData.info.book_cover_data;

            const sidebarContent = `
                <img src="${coverBase64}" alt="${novelData.info.name}" class="book-cover" id="bookCover">
                <h1 class="book-title"><a href="${novelData.info.url}" id="bookLink" target="_blank">${novelData.info.name}</a></h1>
                <div class="book-meta">
                    <span class="author"><i class="fas fa-user-pen"></i> ${novelData.info.author}</span>
                    <span><i class="fas fa-feather"></i> ${novelData.info.author_desc}</span>
                    <span><i class="fas fa-book"></i> ${novelData.info.count_word}</span>
                    <span><i class="fas fa-sync-alt"></i> ${novelData.info.last_update}</span>
                    <span class="status">${novelData.info.label}</span>
                </div>
                <div class="abstract">
                    ${novelData.info.abstract.replace(/\n/g, '<br>')}
                </div>
                <div class="chapter-list">
                    <h3><i class="fas fa-list"></i> 章节列表</h3>
                </div>
            `;

            sidebar.innerHTML = sidebarContent;
            sidebar.querySelector('.chapter-list').appendChild(chapterListContainer);

            // 生成章节列表
            generateChapterList();
        }

        // 图片占位符替换函数
        function replaceImagePlaceholders(content, imgItems) {
            // 正则表达式匹配图片占位符
            const regex = /<&!img\?group_id=(\d+)\/!&>/g;

            return content.replace(regex, (match, groupId) => {
                // 查找匹配的图片描述
                let altText = '';
                let base64Data = '';

                // 遍历所有图片项
                for (const [desc, data] of Object.entries(imgItems)) {
                    // 检查描述是否符合格式
                    if (desc.startsWith(`(${groupId})`)) {
                        base64Data = data;
                        altText = desc.replace(`(${groupId})`, '').trim();
                        break;
                    }
                }

                // 创建图片元素
                if (base64Data) {
                    // 添加图片加载错误处理
                    return `<img src="${base64Data}" alt="${altText}" style="max-width:100%; display:block; margin:15px auto; border-radius: 5px; box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);" onerror="this.onerror=null; this.src='${brokenImageBase64}';">`;
                } else {
                    // 图片数据损坏或不存在
                    return `<img src="${brokenImageBase64}" alt="" style="max-width:100%; display:block; margin:15px auto; border-radius: 5px; box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);">`;
                }
            });
        }

        function addAltTextToImages() {
            const images = document.querySelectorAll('.chapter-content img');
            images.forEach(img => {
                if (!img.parentNode.classList.contains('image-container')) {
                    const altText = img.alt;
                    const container = document.createElement('div');
                    container.className = 'image-container';
                    container.style.margin = '15px auto';
                    container.style.textAlign = 'center';

                    const caption = document.createElement('div');
                    caption.className = 'image-caption';
                    caption.style.marginTop = '8px';
                    caption.style.fontSize = '0.9em';
                    caption.style.color = '#666';
                    caption.textContent = altText;

                    img.parentNode.insertBefore(container, img);
                    container.appendChild(img.cloneNode(true));
                    container.appendChild(caption);
                    img.remove();
                }
            });
        }

        // 生成章节列表
        function generateChapterList() {
            chapterListContainer.innerHTML = '';

            chapterKeys.forEach((key, index) => {
                const chapter = novelData.chapters[key];
                const chapterItem = document.createElement('div');
                chapterItem.className = 'chapter-item';
                if(index === 0) chapterItem.classList.add('active');

                // 添加章节完整性指示
                const statusClass = chapter.integrity ? 'complete' : 'incomplete';
                const statusText = chapter.integrity ? '完整' : '不完整';

                chapterItem.innerHTML = `
                    <div>${key}</div>
                    <div class="chapter-info">
                        <span class="chapter-status ${statusClass}">
                            <i class="fas fa-${chapter.integrity ? 'check-circle' : 'exclamation-circle'}"></i>
                            ${statusText}
                        </span>
                        <a href="${chapter.url}" target="_blank" class="chapter-link">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                `;

                chapterItem.addEventListener('click', (e) => {
                    if (e.target.tagName === 'A' || e.target.tagName === 'I') return;

                    loadChapter(index);
                    document.querySelectorAll('.chapter-item').forEach(item => {
                        item.classList.remove('active');
                    });
                    chapterItem.classList.add('active');

                    // 点击章节后关闭侧边栏
                    sidebar.classList.add('hidden');
                    saveSidebarState();
                });

                chapterListContainer.appendChild(chapterItem);
            });
        }

        // 加载章节内容
        function loadChapter(index) {
            currentChapter = index;
            const chapterKey = chapterKeys[index];
            const chapter = novelData.chapters[chapterKey];

            chapterTitle.textContent = chapterKey;

            // 更新章节元数据
            document.querySelector('.chapter-meta').innerHTML = `
                <span><i class="far fa-calendar"></i> ${chapter.update}</span>
                <span><i class="fas fa-file-word"></i> ${chapter.count_word}</span>
            `;


            // 更新章节完整性指示器
            updateChapterStatus(chapter.integrity);

            // 处理章节内容格式：将段落改为div，每行改为p
            let content = chapter.content;

            // 替换图片占位符
            if (chapter.img_item && Object.keys(chapter.img_item).length > 0) {
                content = replaceImagePlaceholders(content, chapter.img_item);
            }

            const lines = content
                .replace(/\t/g, '  ')
                .split('\n')
                .filter(line => line.trim() !== '');

            let formattedContent = '<div>';
            lines.forEach(line => {
                // 检查是否是图片标签
                if (line.startsWith('<img')) {
                    formattedContent += line;
                } else {
                    formattedContent += `<p>${line}</p>`;
                }
            });
            formattedContent += '</div>';

            // 显示章节内容
            chapterContent.innerHTML = formattedContent;

            // 添加alt文本到图片下方
            addAltTextToImages();

            // 应用段落间距设置
            applyParagraphSpacing();

            // 更新导航按钮状态
            prevBtn.disabled = index === 0;
            nextBtn.disabled = index === chapterKeys.length - 1;

            // 存储阅读位置
            localStorage.setItem(`${namespace}_lastReadChapter`, index);

            // 滚动到顶部
            window.scrollTo(0, 0);

            // 添加章节末尾提示
            if (localStorage.getItem(`${namespace}_chapterEndHint`) === 'true') {
                addChapterEndHint();
            }

            //底部版权作者信息
            bottomAopyrightAuthor.innerHTML=novelData['info']['author']
        }

        // 添加章节末尾提示
        function addChapterEndHint() {
            const chapter = novelData.chapters[chapterKeys[currentChapter]];
            if (currentChapter < chapterKeys.length - 1 && chapter.integrity) {
                const hintElement = document.createElement('div');
                hintElement.className = 'chapter-end-hint';
                hintElement.style.textAlign = 'center';
                hintElement.style.marginTop = '30px';
                hintElement.style.padding = '15px';
                hintElement.style.borderRadius = '8px';
                hintElement.style.backgroundColor = 'rgba(138, 43, 226, 0.1)';
                hintElement.style.color = 'var(--primary)';

                hintElement.innerHTML = `
                    <p>本章已阅读完毕</p>
                    <button id="autoNextBtn" class="nav-btn" style="margin-top: 10px; padding: 8px 20px;">
                        继续阅读下一章 <i class="fas fa-arrow-right"></i>
                    </button>
                `;

                chapterContent.appendChild(hintElement);

                document.getElementById('autoNextBtn').addEventListener('click', () => {
                    if (currentChapter < chapterKeys.length - 1) {
                        loadChapter(currentChapter + 1);
                        updateActiveChapter();
                    }
                });
            }
        }

        // 更新章节完整性状态显示
        function updateChapterStatus(isComplete) {
            if (isComplete) {
                chapterStatus.className = 'chapter-status-indicator complete';
                chapterStatus.innerHTML = '<i class="fas fa-check-circle"></i> 完整';
            } else {
                chapterStatus.className = 'chapter-status-indicator incomplete';
                chapterStatus.innerHTML = '<i class="fas fa-exclamation-circle"></i> 不完整';
            }
        }

        // 保存侧边栏状态到localStorage
        function saveSidebarState() {
            const isHidden = sidebar.classList.contains('hidden');
            localStorage.setItem(`${namespace}_sidebarHidden`, isHidden);
        }

        // 加载侧边栏状态
        function loadSidebarState() {
            const isHidden = localStorage.getItem(`${namespace}_sidebarHidden`) === 'true';
            if (isHidden) {
                sidebar.classList.add('hidden');
                const icon = toggleSidebar.querySelector('i');
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-arrow-right');
            }
        }

        // 初始加载侧边栏内容
        loadSidebarContent();

        // 初始加载第一章或上次阅读位置
        const lastChapter = localStorage.getItem(`${namespace}_lastReadChapter`);
        if(lastChapter) {
            loadChapter(parseInt(lastChapter));
        } else {
            loadChapter(0);
        }

        // 加载侧边栏状态
        loadSidebarState();

        // 导航按钮事件
        prevBtn.addEventListener('click', () => {
            if(currentChapter > 0) {
                loadChapter(currentChapter - 1);
                updateActiveChapter();
            }
        });

        nextBtn.addEventListener('click', () => {
            if(currentChapter < chapterKeys.length - 1) {
                loadChapter(currentChapter + 1);
                updateActiveChapter();
            }
        });

        // 更新活动章节样式
        function updateActiveChapter() {
            document.querySelectorAll('.chapter-item').forEach((item, index) => {
                item.classList.toggle('active', index === currentChapter);
            });
        }

        // 书签功能
        bookmarkBtn.addEventListener('click', () => {
            localStorage.setItem(`${namespace}_lastReadChapter`, currentChapter);
            bookmarkBtn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                bookmarkBtn.innerHTML = '<i class="fas fa-bookmark"></i>';
            }, 1500);
        });

        // 侧边栏切换功能
        toggleSidebar.addEventListener('click', () => {
            sidebar.classList.toggle('hidden');

            // 更新按钮图标
            const icon = toggleSidebar.querySelector('i');
            if (sidebar.classList.contains('hidden')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-arrow-right');
            } else {
                icon.classList.remove('fa-arrow-right');
                icon.classList.add('fa-bars');
            }

            // 保存侧边栏状态
            saveSidebarState();
        });

        // 点击内容区域关闭侧边栏
        document.querySelector('.main-content').addEventListener('click', () => {
            if(!sidebar.classList.contains('hidden')) {
                sidebar.classList.add('hidden');
                const icon = toggleSidebar.querySelector('i');
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-arrow-right');
                saveSidebarState();
            }
        });

        // 设置功能
        settingsBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            settingsPanel.classList.toggle('open');
        });

        closeSettings.addEventListener('click', () => {
            settingsPanel.classList.remove('open');
        });

        // 点击设置面板外部关闭
        document.addEventListener('click', (e) => {
            if (!settingsPanel.contains(e.target) && e.target !== settingsBtn) {
                settingsPanel.classList.remove('open');
            }
        });

        // 防止点击设置面板内部关闭面板
        settingsPanel.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // 字体大小设置
        document.querySelectorAll('.font-size-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.font-size-btn').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                const size = parseFloat(btn.dataset.size);
                document.documentElement.style.setProperty('--font-size', size + 'rem');
                localStorage.setItem(`${namespace}_fontSize`, size);
            });
        });

        // 字体设置
        document.querySelectorAll('.font-family-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.font-family-btn').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                const family = btn.dataset.family;
                document.documentElement.style.setProperty('--font-family', family);
                // 应用到所有相关元素
                document.body.style.fontFamily = family;
                document.querySelector('.chapter-content').style.fontFamily = family;
                localStorage.setItem(`${namespace}_fontFamily`, family);
            });
        });

        // 主题设置
        document.querySelectorAll('.theme-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.theme-btn').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                const theme = btn.dataset.theme;
                // 移除所有主题类
                document.body.className = '';
                // 添加新主题类
                document.body.classList.add(theme + '-theme');
                localStorage.setItem(`${namespace}_theme`, theme);
            });
        });

        // 行高设置
        document.querySelectorAll('.line-height-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.line-height-btn').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                const height = parseFloat(btn.dataset.height);
                document.documentElement.style.setProperty('--line-height', height);
                chapterContent.style.lineHeight = height;
                localStorage.setItem(`${namespace}_lineHeight`, height);
            });
        });

        // 应用段落间距
        function applyParagraphSpacing() {
            const spacing = localStorage.getItem(`${namespace}_paragraphSpacing`) || 1.5;
            document.documentElement.style.setProperty('--paragraph-spacing', spacing);
        }

        // 段落间距设置
        document.querySelectorAll('.paragraph-spacing-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.paragraph-spacing-btn').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                const spacing = parseFloat(btn.dataset.spacing);
                document.documentElement.style.setProperty('--paragraph-spacing', spacing);
                localStorage.setItem(`${namespace}_paragraphSpacing`, spacing);
            });
        });

        // 页面宽度设置
        document.querySelectorAll('.page-width-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.page-width-btn').forEach(b => {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                const width = btn.dataset.width;
                document.documentElement.style.setProperty('--page-width', width);
                document.querySelector('.main-content').style.maxWidth = width;
                localStorage.setItem(`${namespace}_pageWidth`, width);
            });
        });

        // 阅读进度条开关
        progressBarSwitch.addEventListener('change', () => {
            if (progressBarSwitch.checked) {
                readingProgress.style.display = 'block';
            } else {
                readingProgress.style.display = 'none';
            }
            localStorage.setItem(`${namespace}_progressBar`, progressBarSwitch.checked);
        });

        // 章节末尾提示开关
        chapterEndHint.addEventListener('change', () => {
            localStorage.setItem(`${namespace}_chapterEndHint`, chapterEndHint.checked);

            // 立即更新当前章节的提示状态
            const hintElement = chapterContent.querySelector('.chapter-end-hint');
            if (chapterEndHint.checked && !hintElement) {
                addChapterEndHint();
            } else if (!chapterEndHint.checked && hintElement) {
                hintElement.remove();
            }
        });

        // 双击全屏阅读开关
        doubleClickFullscreen.addEventListener('change', () => {
            localStorage.setItem(`${namespace}_doubleClickFullscreen`, doubleClickFullscreen.checked);
        });

        // 双击全屏功能
        chapterContent.addEventListener('dblclick', () => {
            if (localStorage.getItem(`${namespace}_doubleClickFullscreen`) === 'true') {
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(err => {
                        console.error(`无法进入全屏模式: ${err.message}`);
                    });
                } else {
                    if (document.exitFullscreen) {
                        document.exitFullscreen();
                    }
                }
            }
        });

        // 监听滚动事件，更新阅读进度
        window.addEventListener('scroll', updateReadingProgress);

        function updateReadingProgress() {
            const windowHeight = window.innerHeight;
            const documentHeight = Math.max(
                document.body.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.clientHeight,
                document.documentElement.scrollHeight,
                document.documentElement.offsetHeight
            );
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
            const scrollPercentage = (scrollTop / (documentHeight - windowHeight)) * 100;

            readingProgress.style.width = scrollPercentage + '%';
            progressDisplay.textContent = `当前阅读进度: ${Math.round(scrollPercentage)}%`;
        }

        // 加载用户设置
        function loadSettings() {
            // 字体大小
            const savedFontSize = localStorage.getItem(`${namespace}_fontSize`);
            if (savedFontSize) {
                document.documentElement.style.setProperty('--font-size', savedFontSize + 'rem');
                document.querySelectorAll('.font-size-btn').forEach(btn => {
                    if (parseFloat(btn.dataset.size) === parseFloat(savedFontSize)) {
                        btn.classList.add('active');
                    }
                });
            }

            // 字体
            const savedFontFamily = localStorage.getItem(`${namespace}_fontFamily`);
            if (savedFontFamily) {
                document.documentElement.style.setProperty('--font-family', savedFontFamily);
                document.body.style.fontFamily = savedFontFamily;
                document.querySelector('.chapter-content').style.fontFamily = savedFontFamily;
                document.querySelectorAll('.font-family-btn').forEach(btn => {
                    if (btn.dataset.family === savedFontFamily) {
                        btn.classList.add('active');
                    }
                });
            }

            // 主题
            const savedTheme = localStorage.getItem(`${namespace}_theme`);
            if (savedTheme) {
                document.body.className = savedTheme + '-theme';
                document.querySelectorAll('.theme-btn').forEach(btn => {
                    if (btn.dataset.theme === savedTheme) {
                        btn.classList.add('active');
                    }
                });
            }

            // 行高
            const savedLineHeight = localStorage.getItem(`${namespace}_lineHeight`);
            if (savedLineHeight) {
                const height = parseFloat(savedLineHeight);
                document.documentElement.style.setProperty('--line-height', height);
                chapterContent.style.lineHeight = height;
                document.querySelectorAll('.line-height-btn').forEach(btn => {
                    if (parseFloat(btn.dataset.height) === height) {
                        btn.classList.add('active');
                    }
                });
            }

            // 段落间距
            const savedParagraphSpacing = localStorage.getItem(`${namespace}_paragraphSpacing`);
            if (savedParagraphSpacing) {
                const spacing = parseFloat(savedParagraphSpacing);
                document.documentElement.style.setProperty('--paragraph-spacing', spacing);
                document.querySelectorAll('.paragraph-spacing-btn').forEach(btn => {
                    if (parseFloat(btn.dataset.spacing) === spacing) {
                        btn.classList.add('active');
                    }
                });
            }

            // 页面宽度
            const savedPageWidth = localStorage.getItem(`${namespace}_pageWidth`);
            if (savedPageWidth) {
                document.documentElement.style.setProperty('--page-width', savedPageWidth);
                document.querySelector('.main-content').style.maxWidth = savedPageWidth;
                document.querySelectorAll('.page-width-btn').forEach(btn => {
                    if (btn.dataset.width === savedPageWidth) {
                        btn.classList.add('active');
                    }
                });
            }

            // 阅读进度条
            const progressBar = localStorage.getItem(`${namespace}_progressBar`);
            if (progressBar !== null) {
                progressBarSwitch.checked = progressBar === 'true';
                readingProgress.style.display = progressBar === 'true' ? 'block' : 'none';
            }

            // 章节末尾提示
            const endHint = localStorage.getItem(`${namespace}_chapterEndHint`);
            if (endHint !== null) {
                chapterEndHint.checked = endHint === 'true';
            }

            // 双击全屏阅读
            const dblClickFullscreen = localStorage.getItem(`${namespace}_doubleClickFullscreen`);
            if (dblClickFullscreen !== null) {
                doubleClickFullscreen.checked = dblClickFullscreen === 'true';
            }
        }

        // 加载用户设置
        loadSettings();
    });
</script>
</body>

</html>"""
    with open("data/Local/template.html", 'w', encoding='utf-8') as f:
        f.write(template)
    open("data/Local/urls.txt", 'w', encoding='utf-8').close()


# 插入字典到JSON指定位置
def insert_into_dict(original_dict, new_dict, after_key):
    result = {}
    for key, value in original_dict.items():
        result[key] = value
        if key == after_key:
            result.update(new_dict)
    return result


def main():
    # 旧版切换
    if os.path.exists("data/Record/UrlConfig.json"):
        import transform
        transform.init()

    # 格式化
    if not os.path.exists("data/Local"):
        print(f"{Fore.YELLOW}重置中")
        init()


main()
