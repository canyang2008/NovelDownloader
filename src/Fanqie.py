import base64
import json
import random
import re
import time

import requests
import winsound
from DrissionPage.errors import BaseError, WaitTimeoutError
from bs4 import BeautifulSoup, Tag
from colorama import init, Fore
from win10toast import ToastNotifier

init(autoreset=True)


class Fanqie:
    def __init__(self, logger_, class_config, class_driver):

        self.Class_Driver = None
        self.logger = logger_
        self.down_url_list = []
        self.down_title_list = []
        self.pro_url = ''
        self.all_url_list = []
        self.all_title_list = []
        self.novel = {'version': '1.1.0', 'info': {}, 'chapters': {}, "config": {}}
        self.Class_Novel = None
        self.Class_Config = None
        self.user_state_code = -1  # 用户状态码 -1:未登录状态； 0：无vip； 1：标准
        self.Class_Config = class_config
        self.Class_Driver = class_driver

    def user_state_for_html(self, html):
        soup = BeautifulSoup(html, 'lxml')
        user_info_div = soup.find("div", class_="muye-header-right")
        if user_info_div.find('img'):  # 有图片证明已登录
            self.user_state_code = 0
        else:
            self.user_state_code = -1

        if user_info_div.find('i', class_='user-content-vip'):  # 有vip图标时
            self.user_state_code = 1
        else:
            self.user_state_code = 0

        match self.user_state_code:
            case -1:
                print(f"{Fore.YELLOW}番茄账号未登录，下载的小说将不完整")
            case 0:
                print(f"{Fore.YELLOW}番茄账号已登录但无vip，下载的小说将不完整")
            case 1:
                print(f"{Fore.GREEN}番茄账号已登录且有vip")

    def _get_page_for_html(
            self,
            url: str,
            html
    ):
        self.novel = {'version': '1.1.0', 'info': {}, 'chapters': {}, "config": {}}
        # 定位json起始和终点位置
        start = html.find("window.__INITIAL_STATE__=") + len("window.__INITIAL_STATE__=")
        start_html = html[start:]
        end = start_html.find(")()")
        script = start_html[:end].strip()[:-1].strip()[:-1]

        json_data = json.loads(script)
        page_data = json_data.get('page', {})
        name = page_data.get("bookName")
        author = page_data.get("author")
        author_desc = page_data.get("description")
        label_item_str = page_data.get("categoryV2")
        label_item_list = json.loads(label_item_str)
        status = page_data.get("creationStatus")
        label_list = []
        if status == 1:
            label_list.append("连载中")
        else:
            label_list.append("已完结")
        for label_item in label_item_list:
            label_list.append(label_item.get("Name"))
        label = ' '.join(label_list)
        count_word = str(page_data.get("wordNumber")) + "字"
        last_update_of_title = page_data.get("lastChapterTitle")
        last_update_of_time = time.strftime("%Y-%m-%d %H:%M:%S",
                                            time.localtime(int(page_data.get("lastPublishTime"))))
        last_update = f"最近更新：{last_update_of_title} {last_update_of_time}"
        abstract = page_data.get("abstract")
        book_cover_url = page_data.get("thumbUri")
        book_cover_data = base64.b64encode(requests.get(book_cover_url).content).decode("utf-8")
        chapter_list_with_volume = json_data.get("page").get("chapterListWithVolume")
        self.all_title_list = []
        for chapter_list in chapter_list_with_volume:
            for chapter_item in chapter_list:
                self.all_title_list.append(chapter_item.get("title"))
                self.all_url_list.append('https://fanqienovel.com/reader/' + chapter_item.get("itemId"))
        # 更新小说信息
        self.novel['info']['name'] = name
        self.novel['info']['author'] = author
        self.novel['info']['author_desc'] = author_desc
        self.novel['info']['label'] = label
        self.novel['info']['count_word'] = count_word
        self.novel['info']['last_update'] = last_update
        self.novel['info']['abstract'] = abstract
        self.novel['info']['book_cover_data'] = "data:image/png;base64," + book_cover_data
        self.novel['info']['url'] = url
        # 更新下载列表
        self.down_url_list, self.down_title_list = self.all_url_list, self.all_title_list
        return True

    def _get_novel_for_html(
            self,
            title: str,
            url: str,
            html,
    ):

        # 转码表
        transcoding = {"58670": "0", "58413": "1", "58678": "2", "58371": "3", "58353": "4", "58480": "5", "58359": "6",
                       "58449": "7", "58540": "8", "58692": "9", "58712": "a", "58542": "b", "58575": "c", "58626": "d",
                       "58691": "e", "58561": "f", "58362": "g", "58619": "h", "58430": "i", "58531": "j", "58588": "k",
                       "58440": "l", "58681": "m", "58631": "n", "58376": "o", "58429": "p", "58555": "q", "58498": "r",
                       "58518": "s", "58453": "t", "58397": "u", "58356": "v", "58435": "w", "58514": "x", "58482": "y",
                       "58529": "z", "58515": "A", "58688": "B", "58709": "C", "58344": "D", "58656": "E", "58381": "F",
                       "58576": "G", "58516": "H", "58463": "I", "58649": "J", "58571": "K", "58558": "L", "58433": "M",
                       "58517": "N", "58387": "O", "58687": "P", "58537": "Q", "58541": "R", "58458": "S", "58390": "T",
                       "58466": "U", "58386": "V", "58697": "W", "58519": "X", "58511": "Y", "58634": "Z",
                       "58611": "的", "58590": "一", "58398": "是", "58422": "了", "58657": "我", "58666": "不",
                       "58562": "人", "58345": "在", "58510": "他", "58496": "有", "58654": "这", "58441": "个",
                       "58493": "上", "58714": "们", "58618": "来", "58528": "到", "58620": "时", "58403": "大",
                       "58461": "地", "58481": "为", "58700": "子", "58708": "中", "58503": "你", "58442": "说",
                       "58639": "生", "58506": "国", "58663": "年", "58436": "着", "58563": "就", "58391": "那",
                       "58357": "和", "58354": "要", "58695": "她", "58372": "出", "58696": "也", "58551": "得",
                       "58445": "里", "58408": "后", "58599": "自", "58424": "以", "58394": "会", "58348": "家",
                       "58426": "可", "58673": "下", "58417": "而", "58556": "过", "58603": "天", "58565": "去",
                       "58604": "能", "58522": "对", "58632": "小", "58622": "多", "58350": "然", "58605": "于",
                       "58617": "心", "58401": "学", "58637": "么", "58684": "之", "58382": "都", "58464": "好",
                       "58487": "看", "58693": "起", "58608": "发", "58392": "当", "58474": "没", "58601": "成",
                       "58355": "只", "58573": "如", "58499": "事", "58469": "把", "58361": "还", "58698": "用",
                       "58489": "第", "58711": "样", "58457": "道", "58635": "想", "58492": "作", "58647": "种",
                       "58623": "开", "58521": "美", "58609": "总", "58530": "从", "58665": "无", "58652": "情",
                       "58676": "己", "58456": "面", "58581": "最", "58509": "女", "58488": "但", "58363": "现",
                       "58685": "前", "58396": "些", "58523": "所", "58471": "同", "58485": "日", "58613": "手",
                       "58533": "又", "58589": "行", "58527": "意", "58593": "动", "58699": "方", "58707": "期",
                       "58414": "它", "58596": "头", "58570": "经", "58660": "长", "58364": "儿", "58526": "回",
                       "58501": "位", "58638": "分", "58404": "爱", "58677": "老", "58535": "因", "58629": "很",
                       "58577": "给", "58606": "名", "58497": "法", "58662": "间", "58479": "斯", "58532": "知",
                       "58380": "世", "58385": "什", "58405": "两", "58644": "次", "58578": "使", "58505": "身",
                       "58564": "者", "58412": "被", "58686": "高", "58624": "已", "58667": "亲", "58607": "其",
                       "58616": "进", "58368": "此", "58427": "话", "58423": "常", "58633": "与", "58525": "活",
                       "58543": "正", "58418": "感", "58597": "见", "58683": "明", "58507": "问", "58621": "力",
                       "58703": "理", "58438": "尔", "58536": "点", "58384": "文", "58484": "几", "58539": "定",
                       "58554": "本", "58421": "公", "58347": "特", "58569": "做", "58710": "外", "58574": "孩",
                       "58375": "相", "58645": "西", "58592": "果", "58572": "走", "58388": "将", "58370": "月",
                       "58399": "十", "58651": "实", "58546": "向", "58504": "声", "58419": "车", "58407": "全",
                       "58672": "信", "58675": "重", "58538": "三", "58465": "机", "58374": "工", "58579": "物",
                       "58402": "气", "58702": "每", "58553": "并", "58360": "别", "58389": "真", "58560": "打",
                       "58690": "太", "58473": "新", "58512": "比", "58653": "才", "58704": "便", "58545": "夫",
                       "58641": "再", "58475": "书", "58583": "部", "58472": "水", "58478": "像", "58664": "眼",
                       "58586": "等", "58568": "体", "58674": "却", "58490": "加", "58476": "电", "58346": "主",
                       "58630": "界", "58595": "门", "58502": "利", "58713": "海", "58587": "受", "58548": "听",
                       "58351": "表", "58547": "德", "58443": "少", "58460": "克", "58636": "代", "58585": "员",
                       "58625": "许", "58694": "稜", "58428": "先", "58640": "口", "58628": "由", "58612": "死",
                       "58446": "安", "58468": "写", "58410": "性", "58508": "马", "58594": "光", "58483": "白",
                       "58544": "或", "58495": "住", "58450": "难", "58643": "望", "58486": "教", "58406": "命",
                       "58447": "花", "58669": "结", "58415": "乐", "58444": "色", "58549": "更", "58494": "拉",
                       "58409": "东", "58658": "神", "58557": "记", "58602": "处", "58559": "让", "58610": "母",
                       "58513": "父", "58500": "应", "58378": "直", "58680": "字", "58352": "场", "58383": "平",
                       "58454": "报", "58671": "友", "58668": "关", "58452": "放", "58627": "至", "58400": "张",
                       "58455": "认", "58416": "接", "58552": "告", "58614": "入", "58582": "笑", "58534": "内",
                       "58701": "英", "58349": "军", "58491": "侯", "58467": "民", "58365": "岁", "58598": "往",
                       "58425": "何", "58462": "度", "58420": "山", "58661": "觉", "58615": "路", "58648": "带",
                       "58470": "万", "58377": "男", "58520": "边", "58646": "风", "58600": "解", "58431": "叫",
                       "58715": "任", "58524": "金", "58439": "快", "58566": "原", "58477": "吃", "58642": "妈",
                       "58437": "变", "58411": "通", "58451": "师", "58395": "立", "58369": "象", "58706": "数",
                       "58705": "四", "58379": "失", "58567": "满", "58373": "战", "58448": "远", "58659": "格",
                       "58434": "士", "58679": "音", "58432": "轻", "58689": "目", "58591": "条", "58682": "呢"}

        def translate(en_text):  # 转换乱码
            if not en_text: return ''
            de_text = ''
            for index in en_text:
                t1 = ''
                try:
                    t1 = transcoding[str(ord(index))]
                except KeyError:
                    t1 = index
                finally:
                    de_text += t1
            return de_text

        # 定位json起始和终点位置
        start = html.find("window.__INITIAL_STATE__=") + len("window.__INITIAL_STATE__=")
        start_html = html[start:]
        end = start_html.find(")()")
        script = start_html[:end].strip()[:-1].strip()[:-1]

        # json合法化
        script = script.replace('"libra":undefined', '"libra":"undefined"')
        json_data = json.loads(script)
        update_time = "更新时间：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(
            int(json_data.get("reader").get("chapterData").get("firstPassTime"))))
        count_word = "本章字数：" + json_data.get('reader').get("chapterData").get("chapterWordNumber")
        parent_soup = BeautifulSoup(html, 'lxml')
        if parent_soup.find('div', class_='muye-to-fanqie'):  # 完整性检查
            integrity = False
        else:
            integrity = True
        # 减小范围以准确定位text和img
        html_content = str(parent_soup.find('div', class_='muye-reader-content noselect'))
        soup = BeautifulSoup(translate(html_content), 'lxml')
        img_counter = 0
        img_dict = {}

        """处理图片"""
        # 处理所有图片标签
        img_tags = soup.find_all('img')
        for img in img_tags:
            img_counter += 1
            group_id = img_counter

            # 获取图片描述
            picture_desc = ""
            parent = img.parent
            while parent and isinstance(parent, Tag):
                # 检查是否有pictureDesc兄弟元素
                if parent.name == 'div' and parent.get('data-fanqie-type') == 'image':
                    picture_desc_tag = parent.find('p', class_='pictureDesc')
                    if (picture_desc_tag and
                            isinstance(picture_desc_tag, Tag) and
                            picture_desc_tag.get('group-id') == str(group_id)):
                        picture_desc = picture_desc_tag.get_text(strip=True)
                        break

                # 检查当前元素是否有pictureDesc类
                if (parent.name == 'p' and
                        'pictureDesc' in (parent.get('class') or [])):
                    picture_desc = parent.get_text(strip=True)
                    break

                parent = parent.parent

            # 构建字典键
            if picture_desc:
                dict_key = f"({group_id}) {picture_desc}"
            else:
                dict_key = f"({group_id})"

            img_url = img.get('src', '')
            img_data = base64.b64encode(requests.get(img_url).content).decode("utf-8")
            img_data = "data:image/png;base64," + img_data
            # 添加到图片字典
            img_dict[dict_key] = img_data

            # 替换图片为指定文本 - 创建一个新的 NavigableString
            replacement_text = soup.new_string(f'<&!img?group_id={group_id}/!&>')
            img.replace_with(replacement_text)

        # 提取所有段落文本，保留<img>替换标记
        content_div = soup.find('div', class_='muye-reader-content')
        text_content = []
        if content_div:
            # 遍历所有元素
            for element in content_div.descendants:
                # 处理字符串元素
                if isinstance(element, str):
                    text = element.strip()
                    if text:
                        # 检查是否是图片替换标记
                        if text.startswith('<&!img?group_id=') and text.endswith('/!&>'):
                            text_content.append(text)
                        else:
                            text_content.append(text)

                # 处理标签元素
                elif isinstance(element, Tag) and element.name == 'p':
                    # 跳过图片描述段落
                    if 'pictureDesc' in (element.get('class') or []):
                        continue

                    text = element.get_text(strip=True)
                    if text:
                        text_content.append(text)

        text_content = [text_content[i] for i in range(0, len(text_content), 2)]  # 去除重复文本
        novel_content = "\n".join(text_content)
        # 赋值
        self.novel['chapters'][title] = {
            'url': url,
            'update': update_time,
            'count_word': count_word,
            'content': novel_content.replace('已经是最新一章',
                                             '') if '已经是最新一章' in novel_content else novel_content,
            'integrity': integrity,
            'img_item': img_dict
        }
        return True

    def _get_novel_for_oiapi(self, index, chapter_url, page_url):
        headers = {
            'Referer': "https://oiapi.net/doc/?id=115",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
            "Origin": "https://oiapi.net",
        }
        # 以POST获取内容
        post_data = {
            "chapter": str(index),
            "id": re.search(r'page/(\d+)', page_url).group(1),
            "key": self.Class_Config.Api_key,
            "type": "json"
        }
        response = requests.post("https://oiapi.net/api/FqRead", data=post_data, headers=headers).json()
        message = response['message']
        data = response.get('data')
        # 没有键data说明出现问题
        if not data:
            print(f"oiapi出现错误\nmessage:{message}")
            return False
        else:
            chapter_data = data[0]
            title = chapter_data['chapter_title']
            update_time = time.strftime("%Y-%m-%d %H:%M", time.localtime(chapter_data['time']))  # 更新时间
            count_word = chapter_data['word_number']  # 章节字数
            content = chapter_data['content']  # 小说内容
            self.Class_Novel['chapters'][title] = {
                "url": chapter_url,
                "update": f"更新时间：{update_time}",
                "count_word": f"本章字数：{count_word}",
                "content": content.replace('已经是最新一章',
                                           '') if '已经是最新一章' in content else content,
                'integrity': True,
                'img_item': {}  # api无图片
            }
            return True

    def _get_soup_for_browser(self, url):
        if "page" in url:
            class_name = ".page-directory-content"  # 番茄目录页
        elif "reader" in url:
            class_name = ".muye-reader-content noselect"  # 番茄章节内容页
        else:
            class_name = None
        try:
            self.Class_Driver.tab.get(url)  # 访问
            time.sleep(random.uniform(self.Class_Config.Delay[0], self.Class_Config.Delay[1]))  # 延迟
            if not self.Class_Driver.tab.states.is_alive: raise BaseError
            self.Class_Driver.tab.wait.eles_loaded(
                class_name, raise_err=True)  # 等待加载
            html = self.Class_Driver.tab.raw_data
            return html
        except WaitTimeoutError:
            # 验证码框架
            if self.Class_Driver.tab.get_frames():
                toast = ToastNotifier()
                toast.show_toast(
                    title="验证码拦截",
                    msg="请完成验证码",
                    icon_path=None,
                    duration=3
                )
                if self.Class_Config.Play_completion_sound:
                    winsound.MessageBeep(winsound.MB_OK)
                    time.sleep(1)
                    winsound.MessageBeep(winsound.MB_OK)
                input("请完成验证码...\n完成后按Enter继续")
                return self._get_soup_for_browser(url)
        except BaseError:
            self.Class_Driver.tab = self.Class_Driver.run()
            return self._get_soup_for_browser(url)
        return True


    def get_page(self, url):  # 获取小说信息和所有链接与标题

        if self.Class_Config.Get_mode == 0:  # 浏览器模式
            html = self._get_soup_for_browser(url)
            self.user_state_for_html(html)  # 用户状态
        else:
            html = requests.get(url).text
            if "page-directory-content" not in html:
                print("获取所有目录页出现问题")
                return False
        self._get_page_for_html(url, html)
        return True

    def download(self, title, chapter_url, index=0, page_url=None):
        if self.Class_Config.Get_mode == 0:     # 浏览器模式
            html = self._get_soup_for_browser(chapter_url)  # 获取html文本
            self._get_novel_for_html(title, chapter_url, html)

        else:
            match self.Class_Config.Api_option:
                case 'oiapi':
                    if not self._get_novel_for_oiapi(index, chapter_url, page_url): return False
        return True
