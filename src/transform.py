import json
import os

import msgpack


def init():
    with open("data/Record/UrlConfig.json", "r", encoding="utf-8") as f:
        url_config = json.load(f)
    with open("data/Record/SettingConfig.json", "r", encoding="utf-8") as f:
        setting = json.load(f)
    first_user = list(url_config.keys())[1]
    manage = {
        "VERSION": "1.1.0",
        "README": "",
        "USER": first_user,
        "USERS": {}
    }
    user_config_part = {
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
                3
            ],
            "Port": 9444,
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
                "one_file": False
            }
        },
        "Unprocess": []
    }
    mems = {}
    port = 9444
    for user in url_config.keys():
        mems = {"Version": "1.1.0"}
        if user == 'Version':
            continue

        port += 1
        user_config_part["Browser"]["Port"] = port
        manage['USERS'][user] = {
            "User_config_path": f"data/Local/{user}/UserConfig.json",
            "User_data_dir": f"data/Local/{user}/User Data",
            "Base_dir": f"data/Local/{user}/json"}

        os.makedirs(f"data/Local/{user}", exist_ok=True)

        with open(f"data/Local/{user}/UserConfig.json", "w", encoding="utf-8") as f:
            user_config = {
                "Version": "1.1.0",
                "User_name": user,
                "Group": "Default",
                "README": ""
            }
            user_config.update(user_config_part)
            f.write(json.dumps(user_config, ensure_ascii=False, indent=4))
        for group in url_config[user].keys():
            for url in url_config[user][group].keys():
                file_name = url_config[user][group][url]["Name"] + '.json'
                with open(os.path.join(os.getenv("LOCALAPPDATA"), 'CyNovelbase', "data", user, "json", file_name),
                          "rb") as f:
                    try:
                        msg_data = msgpack.load(f, strict_map_key=False)
                    except msgpack.UnpackException:
                        print("有一文件：" + file_name + "未转化成功，需重新下载或自行转化")
                        continue
                config = url_config[user][group][url]
                new_config = {
                    "Version": "1.1.0",
                    "Name": config['Name'],
                    "Group": group,
                    "State": config['State'],
                    "Max_retry": 3,
                    "Timeout": 10,
                    "Interval": 2,
                    "Delay": config['Wait_time'],
                    "Save_method": config['Save_method'],
                    "First_timestamp": config['First_timestamp'],
                    "First_time": config['First_time'],
                    "Last_control_timestamp": config['Last_control_timestamp'],
                    "Last_control_time": config['Last_control_time'],
                }
                if group not in mems.keys():
                    mems[group] = {}
                mems[group][url] = config['Name']
                msg_data['config'] = new_config
                new_json = json.dumps(msg_data, ensure_ascii=False, indent=4)
                os.makedirs(f"data/Local/{user}/json", exist_ok=True)
                with open(f"data/Local/{user}/json/mems.json", "w", encoding="utf-8") as f:
                    json.dump(mems, f, ensure_ascii=False, indent=4)
                with open(f"data/Local/{user}/json/{file_name}", "w", encoding="utf-8") as f:
                    f.write(new_json)
        with open(f"data/Local/manage.json", "w", encoding="utf-8") as f:
            json.dump(manage, f, ensure_ascii=False, indent=4)
