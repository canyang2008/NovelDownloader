import time

enable=True
import json
import os
import re
from typing import Any
from novel_downloader.core.downloader import ChromeDownloader, APIDownloader, RequestsDownloader
from novel_downloader.models import DownloadMode
from novel_downloader.models.novel import Novel,Chapter
from novel_downloader.parsers import APIError, FeatureNotSupportedError
from novel_downloader.parsers.base import BaseParser
import requests
from bs4 import BeautifulSoup, Tag
"""
/html/body/div[1]/div/div[2]/div/div/div[4]/div[1]/div[2]/div[1]/span
/html/body/div[1]/div/div[2]/div/div/div[4]/div[2]/div[2]/div[1]/span
"""

# 小说内容转码表
content_transcoding = {"58670": "0", "58413": "1", "58678": "2", "58371": "3", "58353": "4", "58480": "5", "58359": "6",
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

# 搜索页面的转码表（Time consuming for cracking：3h）
search_transcoding = {'58422': '0', '58400': '1', '58646': '2', '58381': '3', '58355': '4', '58707': '5', '58530': '6',
                      '58538': '7', '58685': '8', '58415': '9', '58614': 'a', '58620': 'b', '58487': 'c', '58452': 'd',
                      '58674': 'e', '58535': 'f', '58406': 'g', '58375': 'h', '58601': 'i', '58498': 'j', '58708': 'k',
                      '58475': 'l', '58514': 'm', '58700': 'n', '58606': 'o', '58650': 'p', '58582': 'q', '58659': 'r',
                      '58345': 's', '58709': 't', '58407': 'u', '58474': 'v', '58376': 'w', '58546': 'x', '58529': 'y',
                      '58494': 'z', '58476': 'A', '58353': 'B', '58622': 'C', '58594': 'D', '58531': 'E', '58590': 'F',
                      '58389': 'G', '58675': 'H', '58607': 'I', '58508': 'J', '58393': 'K', '58460': 'L', '58412': 'M',
                      '58403': 'N', '58473': 'O', '58453': 'P', '58704': 'Q', '58519': 'R', '58466': 'S', '58658': 'T',
                      '58356': 'U', '58525': 'V', '58548': 'W', '58570': 'X', '58497': 'Y', '58409': 'Z', '58454': '的',
                      '58549': '一', '58484': '是', '58504': '了', '58581': '我', '58656': '不', '58578': '人',
                      '58349': '在', '58350': '他', '58711': '有', '58694': '这', '58587': '个', '58534': '上',
                      '58360': '们', '58465': '来', '58547': '到', '58600': '时', '58643': '大', '58706': '地',
                      '58568': '为', '58495': '子', '58380': '中', '58644': '你', '58405': '说', '58551': '生',
                      '58471': '国', '58378': '年', '58631': '着', '58490': '就', '58513': '那', '58647': '和',
                      '58386': '要', '58633': '她', '58640': '出', '58591': '也', '58488': '得', '58469': '里',
                      '58563': '后', '58479': '自', '58565': '以', '58712': '会', '58598': '家', '58518': '可',
                      '58702': '下', '58562': '而', '58496': '过', '58673': '天', '58612': '去', '58351': '能',
                      '58586': '对', '58561': '小', '58372': '多', '58610': '然', '58383': '于', '58477': '心',
                      '58576': '学', '58501': '么', '58575': '之', '58696': '都', '58485': '好', '58639': '看',
                      '58690': '起', '58599': '发', '58605': '当', '58511': '没', '58550': '成', '58653': '只',
                      '58526': '如', '58688': '事', '58683': '把', '58596': '还', '58698': '用', '58446': '第',
                      '58651': '样', '58445': '道', '58541': '想', '58347': '作', '58489': '种', '58556': '开',
                      '58411': '美', '58663': '总', '58671': '从', '58480': '无', '58617': '情', '58398': '己',
                      '58390': '面', '58655': '最', '58449': '女', '58554': '但', '58522': '现', '58470': '前',
                      '58472': '些', '58502': '所', '58388': '同', '58560': '日', '58693': '手', '58703': '又',
                      '58413': '行', '58491': '意', '58368': '动', '58392': '方', '58408': '期', '58440': '它',
                      '58687': '头', '58521': '经', '58539': '长', '58459': '儿', '58463': '回', '58574': '位',
                      '58391': '分', '58664': '爱', '58615': '老', '58597': '因', '58533': '很', '58414': '给',
                      '58505': '名', '58699': '法', '58436': '间', '58520': '斯', '58668': '知', '58402': '世',
                      '58394': '什', '58418': '两', '58377': '次', '58444': '使', '58665': '身', '58367': '者',
                      '58588': '被', '58363': '高', '58448': '已', '58616': '亲', '58369': '其', '58657': '进',
                      '58427': '此', '58542': '话', '58434': '常', '58649': '与', '58366': '活', '58359': '正',
                      '58637': '感', '58438': '见', '58524': '明', '58462': '问', '58627': '力', '58624': '理',
                      '58365': '尔', '58691': '点', '58416': '文', '58567': '几', '58435': '定', '58397': '本',
                      '58613': '公', '58382': '特', '58660': '做', '58410': '外', '58439': '孩', '58641': '相',
                      '58537': '西', '58713': '果', '58527': '走', '58417': '将', '58536': '月', '58384': '十',
                      '58635': '实', '58425': '向', '58362': '声', '58516': '车', '58364': '全', '58552': '信',
                      '58585': '重', '58566': '三', '58545': '机', '58634': '工', '58630': '物', '58433': '气',
                      '58515': '每', '58352': '并', '58589': '别', '58692': '真', '58432': '打', '58619': '太',
                      '58652': '新', '58608': '比', '58358': '才', '58654': '便', '58540': '夫', '58395': '再',
                      '58592': '书', '58512': '部', '58447': '水', '58426': '像', '58510': '眼', '58401': '等',
                      '58618': '体', '58486': '却', '58670': '加', '58623': '电', '58370': '主', '58697': '界',
                      '58523': '门', '58714': '利', '58544': '海', '58507': '受', '58677': '听', '58499': '表',
                      '58604': '德', '58430': '少', '58357': '克', '58483': '代', '58572': '员', '58419': '许',
                      '58593': '稜', '58492': '先', '58348': '口', '58679': '由', '58571': '死', '58429': '安',
                      '58595': '写', '58457': '性', '58559': '马', '58482': '光', '58428': '白', '58602': '或',
                      '58603': '住', '58695': '难', '58373': '望', '58396': '教', '58528': '命', '58437': '花',
                      '58399': '结', '58583': '乐', '58636': '色', '58628': '更', '58629': '拉', '58558': '东',
                      '58464': '神', '58638': '记', '58701': '处', '58682': '让', '58662': '母', '58555': '父',
                      '58424': '应', '58441': '直', '58361': '字', '58678': '场', '58478': '平', '58371': '报',
                      '58421': '友', '58456': '关', '58374': '放', '58689': '至', '58420': '张', '58569': '认',
                      '58503': '接', '58705': '告', '58385': '入', '58553': '笑', '58557': '内', '58423': '英',
                      '58481': '军', '58645': '侯', '58715': '民', '58710': '岁', '58669': '往', '58431': '何',
                      '58517': '度', '58450': '山', '58609': '觉', '58642': '路', '58564': '带', '58621': '万',
                      '58387': '男', '58681': '边', '58442': '风', '58451': '解', '58458': '叫', '58684': '任',
                      '58506': '金', '58680': '快', '58632': '原', '58611': '吃', '58461': '妈', '58543': '变',
                      '58455': '通', '58666': '师', '58493': '立', '58584': '象', '58443': '数', '58468': '四',
                      '58626': '失', '58509': '满', '58532': '战', '58577': '远', '58661': '格', '58354': '士',
                      '58579': '音', '58667': '轻', '58573': '目', '58686': '条', '58580': '呢'}

def translate(en_text,coding = 0):  # 转换乱码
    if not en_text: return ''
    de_text = ''
    if not coding:
        transcoding = content_transcoding
    else:
        transcoding = search_transcoding
    for index in en_text:
        t1 = ''
        try:
            t1 = transcoding[str(ord(index))]
        except KeyError:
            t1 = index
        finally:
            de_text += t1
    return de_text

def user_status(html):
    soup = BeautifulSoup(html, 'lxml')
    user_info_div = soup.find("div", class_="muye-header-right")
    if user_info_div:
        if user_info_div.find('img'):  # 有图片证明已登录
            user_state_code = 0
        else:
            user_state_code = -1
        if user_info_div.find('i', class_='user-content-vip'):  # 有vip图标时
            user_state_code = 1
    else:
        user_state_code = -1
    return user_state_code


# 通过html获取小说相关信息的基类
class _FanqieForHtml(BaseParser):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
        self.index = 0
        self.batch_size = 1

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str,Any]]:
        soup = BeautifulSoup(content, 'lxml')
        search_result_list = soup.find("div", class_="muye-search-book-list").find_all("div",class_="search-book-item")
        result = []
        button_index = 0
        for search_result_item in search_result_list:
            book_img_url = None
            book_name = None
            author = None
            tags_str = None
            count_str = None
            reading_numbers_str = None
            description = None
            latest_chapter = None
            time_str = None
            search_result_item = search_result_item.find("div", class_="book-item-text")
            img_div = soup.find("div", class_="book-cover")
            if img_div:
                book_img_url = img_div.find("img")["src"]
            button_index += 1
            button_xpath = f"/html/body/div[1]/div/div[2]/div/div/div[4]/div[{button_index}]/div[2]/div[1]/span"

            for div in search_result_item:
                if "title" in div["class"]:
                    book_name = translate(div.get_text(),1)
                    continue
                elif "desc" in div["class"] and "abstract" not in div["class"]:
                    author = translate(div.find("span", class_="highlight-text").get_text(),1)
                    tags_str = translate(div.find_all("span", class_="span")[0].get_text(),1)
                    count_and_reading = translate(div.find_all("span", class_="span")[1].get_text(),1)
                    count_str = count_and_reading.split("·")[0]
                    reading_numbers_str = count_and_reading.split("·")[1]
                elif "desc" in div["class"] and "abstract" in div["class"]:
                    description = translate(div.find("span",class_="highlight-text").get_text(),1)
                    continue
                elif "footer" in div["class"]:
                    lastest_chapter_and_time = div.find_all("span")
                    latest_chapter = lastest_chapter_and_time[0].get_text()
                    time_str = lastest_chapter_and_time[1].get_text()

            result.append({
                "name": book_name,
                "author": author,
                "tags": tags_str,
                "word_count": count_str,
                "read_count": reading_numbers_str,
                "description": description,
                "latest_chapter": latest_chapter,
                "update_time": time_str,
                "cover_url": book_img_url,
                "need_unlock": False,
                "platform":"番茄小说网",
                "button_xpath":button_xpath
            })
        return result

    def parse_novel_info(self, content, **kwargs) -> Novel | None:
        # 定位json起始和终点位置
        start = content.find("window.__INITIAL_STATE__=") + len("window.__INITIAL_STATE__=")
        start_html = content[start:]
        end = start_html.find(")()")
        script = start_html[:end].strip()[:-1].strip()[:-1]

        json_data = json.loads(script)
        page_data = json_data.get('page')
        book_url = f"https://fanqienovel.com/page/{page_data['bookId']}"
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
        count_word = page_data.get("wordNumber")
        last_update_of_title = page_data.get("lastChapterTitle")
        last_update_of_time = int(page_data.get("lastPublishTime"))
        abstract = page_data.get("abstract")
        book_cover_url = page_data.get("thumbUri")
        book_cover_data = requests.get(book_cover_url).content
        novel = Novel(url=book_url,
                      name=name,
                      author=author,
                      author_description=author_desc,
                      tags=label_list,
                      description=abstract,
                      count=count_word,
                      last_update_chapter=last_update_of_title,
                      last_update_time=last_update_of_time,
                      cover_image_data=book_cover_data
                      )

        chapter_list_with_volume = json_data.get("page").get("chapterListWithVolume")
        for chapters_list in chapter_list_with_volume:
            for chapter_item in chapters_list:
                title = chapter_item["title"]
                chapter_url = 'https://fanqienovel.com/reader/' + chapter_item.get("itemId")
                first_pass_time = int(chapter_item.get("firstPassTime"))
                real_chapter_order = int(chapter_item.get("realChapterOrder"))
                volume_name = chapter_item.get("volume_name")
                chapter = Chapter(title=title,
                                  url=chapter_url,
                                  volume=volume_name,
                                  order=real_chapter_order,
                                  timestamp=first_pass_time)
                novel.update(chapter)
        return novel

    def parse_chapter_content(self, content, orders: list[int], **kwargs) -> tuple[Chapter | None]:

        # 定位json起始和终点位置
        if BeautifulSoup(content, "html.parser").find("div",class_="no-content"):
            return (None, )
        start = content.find("window.__INITIAL_STATE__=") + len("window.__INITIAL_STATE__=")
        start_html = content[start:]
        end = start_html.find(")()")
        script = start_html[:end].strip()[:-1].strip()[:-1]
        # json合法化
        script = script.replace('"libra":undefined', '"libra":"undefined"')
        json_data = json.loads(script)
        url = "https://fanqienovel.com/reader/"+(json_data.get("reader").get("chapterData").get("bookId"))
        title = json_data.get("reader").get("chapterData").get("title")
        count = json_data.get("reader").get("chapterData").get("chapterWordNumber")
        update_timestamp = int(json_data.get("reader").get("chapterData").get("firstPassTime"))
        parent_soup = BeautifulSoup(content, 'lxml')
        if parent_soup.find('div', class_='muye-to-fanqie'):  # 完整性检查
            integrity = False
        else:
            integrity = True
        # 减小范围以准确定位text和img
        html_content = str(parent_soup.find('div', class_='muye-reader-content noselect'))
        soup = BeautifulSoup(translate(html_content), 'lxml')
        img_counter = 0
        img_items = []

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
            img_data = requests.get(img_url).content
            # 添加到图片元组
            img_items.append((dict_key,img_data))
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
        if '已经是最新一章' in novel_content:
            novel_content = novel_content.replace('已经是最新一章', '')
        chapter = Chapter(
            title=title,
            url=url,
            order=orders[0],
            images=img_items,
            count = int(count),
            timestamp = update_timestamp,
            content=novel_content,
            is_complete = integrity,
        )
        # 赋值
        return (chapter,)

class FanqieForBrowser(_FanqieForHtml):
    def __init__(self,downloader:ChromeDownloader,**kwargs):
        super().__init__(**kwargs)
        self.novel = None
        self.user_status:int = -1
        self.downloader = downloader
        self.verify_prompted = False

    def needs_verification(self, html):
        soup = BeautifulSoup(html, 'lxml')
        if soup.find("iframe") or soup.find("frame"):
            if not self.verify_prompted:
                print("需要完成验证码")
                self.verify_prompted = True
            return True
        else:
            return False

    def parse_search_info(self, content, page=0, download_choice:int=None, **kwargs) -> list[dict[str,Any]] | str | None:
        search_url = f"https://fanqienovel.com/search/{content}"
        temp_delay = self.downloader.delay
        self.downloader.delay = (2,4)
        if page >= 1:
            next_page_xpath = f"/html/body/div[1]/div/div[2]/div/div/div[5]/ul/li[{page+1}]"
            self.downloader.page.ele(f"xpath:{next_page_xpath}").click()
        html = self.downloader.get(search_url)
        self.downloader.delay = temp_delay
        result =  super().parse_search_info(content=html, page=page, download_choice=None, **kwargs)
        if not result:
            return None
        if download_choice is not None:
            book_info = result[download_choice]
            button_xpath = book_info["button_xpath"]
            self.downloader.page.ele(f"xpath:{button_xpath}").click()
            book_url = self.downloader.driver.get_tab().url
            return book_url
        else:return result

    def parse_novel_info(self, content, **kwargs) -> Novel:
        html = self.downloader.get(url=content)
        while True:
            if self.downloader.page.url != content:
                html = self.downloader.get(url=content)
            else:break
        self.user_status = user_status(html)
        self.novel = super().parse_novel_info(content=html)
        return self.novel

    def parse_chapter_content(self, content, orders: list[int], **kwargs) -> tuple[Chapter | None]:
        del content
        download_url = self.novel[orders[0]].url
        while True:
            html = self.downloader.get(url=download_url)
            if self.needs_verification(html):
                time.sleep(3)
                continue
            else:
                break
        chapters = super().parse_chapter_content(content=html, orders=orders, **kwargs)
        return chapters

class FanqieForOiapi(BaseParser):
    def __init__(self,downloader:APIDownloader,**kwargs):
        super().__init__(**kwargs)
        self.batch_size = 5
        self.downloader = downloader
        self.novel = None
        self.search_result = None

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str,Any]] | str | None:
        result = []
        if download_choice is not None:
            book_url = self.search_result[download_choice]["book_url"]
            return book_url
        post_data = {
            "page": page,
            "keyword": content,
            "key": self.downloader.key,
            "type": "json"
        }
        content = self.downloader.get(url="https://oiapi.net/api/FqRead", post_data=post_data)
        if content.get("data"):
            book_info_list = content.get("data")
            for book_info in book_info_list:
                book_id = book_info.get("id")
                book_name = book_info.get("title")
                author = book_info.get("author")
                count = book_info.get("word_number")
                reading_numbers = book_info.get("read_count")
                tags = book_info.get("tags")
                description = book_info.get("docs")
                book_cover_url = book_info.get("thumb")
                chapters_count = book_info.get("serial")
                latest_chapter = None
                time_str = None
                result.append({
                    "name": book_name,
                    "author": author,
                    "tags": tags,
                    "word_count": count,
                    "read_count": reading_numbers,
                    "chapters_count": chapters_count,
                    "description": description,
                    "latest_chapter": latest_chapter,
                    "update_time": time_str,
                    "cover_url": book_cover_url,
                    "book_url": f"https://fanqienovel.com/page/{book_id}",
                    "need_unlock": False,
                    "platform":"番茄小说网"
                })
        self.search_result = result
        return result

    def parse_chapter_content(self, content, orders: list[int], **kwargs) -> tuple[Chapter | None]:
        def get_chapters_recursion(current_orders:list[int]):
            post_data = {
                "chapter": ",".join(str(i) for i in current_orders),
                "id": re.search(r'page/(\d+)', self.novel.url).group(1),
                "key": self.downloader.key,
                "type": "json"
            }
            response = self.downloader.get(url="https://oiapi.net/api/FqRead",post_data=post_data)
            message = response['message']
            data_list = response.get('data')
            if not data_list:
                if message == "请检测章节选择是否正确":
                    if len(current_orders) > 1:
                        current_orders = current_orders[:len(current_orders)-1]
                        return get_chapters_recursion(current_orders=current_orders)
                    else:
                        return (None,)
                raise APIError("OIAPI",f"oiapi出现错误\nmessage:{message}")
            else:
                return data_list
        data_list = get_chapters_recursion(orders)
        result = []
        index = 0
        for data in data_list:
            order = orders[index]

            chapter_data = data
            chapter_url = f"https://fanqienovel.com/chapter/{chapter_data['chapter_id']}"
            title = chapter_data['chapter_title']
            volume = chapter_data['volume']
            update_time: int = chapter_data['time']
            count_word: int = chapter_data['word_number']
            content = chapter_data['content']
            if '已经是最新一章' in content:
                content = content.replace('已经是最新一章', '')
            chapter = Chapter(title=title,
                              url=chapter_url,
                              order=order,
                              volume=volume,
                              content=content,
                              timestamp=update_time,
                              count=count_word,
                              is_complete=True)
            result.append(chapter)
            index += 1
        needed = len(orders)-len(data_list)
        result.extend([None]*needed)
        return tuple(result)

    def parse_novel_info(self, content, **kwargs) -> Novel | None:

        message = content['message']
        data = content.get('data')
        if not data:
            raise APIError("OIAPI",f"oiapi message:{message}")
        else:
            url = f"https://fanqienovel.com/page/{data.get('id')}"
            book_cover_data = requests.get(data.get('thumb')).content
            name = data.get('title')
            author = data.get('author')
            word_number = int(data.get('word_number'))
            # 更新小说信息
            self.novel = Novel(url=url,
                               name=name,
                               author=author,
                               author_description=None,
                               count=word_number,
                               description=data.get('docs'),
                               cover_image_data=book_cover_data,
                               )
            return self.novel

class FanqieForReq(_FanqieForHtml):

    def __init__(self,downloader:RequestsDownloader,**kwargs):
        super().__init__(**kwargs)
        self.user_status:int = -1
        self.downloader = downloader
        self.novel = None

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict]:
        raise FeatureNotSupportedError("番茄小说网不支持Requests以获取搜索结果")

    def parse_chapter_content(self, content, orders: list[int], **kwargs) -> tuple[Chapter | None]:
        url = self.novel[orders[0]].url
        html = self.downloader.get(url=content)
        while True:
            if self.downloader.page.url != content:
                html = self.downloader.get(url=url)
            else:break
        chapters = super().parse_chapter_content(content=html, orders=orders, **kwargs)
        return chapters
    def parse_novel_info(self, content, **kwargs) -> Novel:
        html = self.downloader.get(url=content)
        self.user_status = user_status(html)
        self.novel = super().parse_novel_info(content=content, **kwargs)
        return self.novel

class FanqieParser(BaseParser):
    def __init__(self,downloader:ChromeDownloader|APIDownloader|RequestsDownloader,**kwargs):
        super().__init__(**kwargs)
        if downloader.MODE == DownloadMode.BROWSER:
            self.__parser = FanqieForBrowser(downloader = downloader,**kwargs)
        elif downloader.MODE == DownloadMode.API:
            self.__parser = FanqieForOiapi(downloader = downloader,**kwargs)
        elif downloader.MODE == DownloadMode.REQUESTS:
            self.__parser = FanqieForReq(downloader = downloader,**kwargs)
        self.batch_size = self.__parser.batch_size

    def update(self,novel:Novel = None,downloader:ChromeDownloader|APIDownloader|RequestsDownloader = None,**kwargs):
        if novel:
            self.__parser.novel = novel
        if downloader:
            self.__parser.downloader = downloader

    def parse_search_info(self, content, page=0, download_choice=None, **kwargs) -> list[dict[str,Any]] | str | None:
        return self.__parser.parse_search_info(content=content, page=page, download_choice=download_choice, **kwargs)
    def parse_novel_info(self, content, **kwargs) -> Novel:
        return self.__parser.parse_novel_info(content=content,**kwargs)
    def parse_chapter_content(self, content: str, orders: list[int], **kwargs) -> tuple[Chapter | None]:
        return self.__parser.parse_chapter_content(content=content, orders=orders, **kwargs)
