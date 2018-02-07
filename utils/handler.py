import re
import json
import datetime
import requests
from bs4 import BeautifulSoup

import smtplib
import email
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.utils import make_msgid

from sched import scheduler

from utils.config import HandlerConfig


_session = requests.session()

CONFIG = HandlerConfig()

TARGET = {
    "url": "https://search.smzdm.com/?c=home&s={}",
    "channels": ["国内优惠", "海淘优惠", "发现优惠", "好价频道"],
}

HEADERS = {
    # "referer": "https://www.smzdm.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/63.0.3239.132 Safari/537.36",
}


class error_handler:

    def __init__(self, func):
        self.func = func

    def __get__(self, ins, cls):
        def wrapper(*args, **kwargs):
            try: return self.func(ins, *args, **kwargs)
            # TODO: log
            except Exception: pass
        return wrapper


class EmailTemplate:

    _template = ("<h3>{name}({grocery})</h3>"
                 "<div><a href='{link}'><img src='cid:{cid}'></a></div>"
                 "<div><p>价格：￥{price}; 发布日期：{publish}</p></div>"
                 "<hr>")

    def __init__(self, html):
        assert isinstance(html, str)
        self.soup = BeautifulSoup(html, "html.parser")

        self.message = EmailMessage()
        self.message["From"] = CONFIG["sender"]
        self.message["To"] = ",".join(CONFIG["receivers"])
        self.message["Subject"] = CONFIG["subject"]

    def lis(self):
        for li in self.soup.select("ul[id=feed-main-list] li"):
            yield li

    @staticmethod
    def channel(li):
        # 商品所属购物频道
        return li.select_one("div[class=z-feed-img] span").string

    """
    @staticmethod
    def next(li):
        return li.select_one("div[class=feed-link-btn-inner] a")[0]
    """

    @staticmethod
    def data(li):
        # 商品在购物平台中的地址
        go_buy = li.select_one("div[class=feed-link-btn-inner] a")
        data = re.findall(r"push\((.*?)\)", go_buy["onclick"])[1]
        return json.loads(data.replace("'", '"'))

    @staticmethod
    def link(li):
        # 商品在 smzdm 中的地址
        return li.select_one("div[class=z-feed-img] a").get("href", "").strip()

    @staticmethod
    def publish(li):
        # 商品发布日期
        return li.select_one("span[class=feed-block-extras]").contents[0].strip()

    @staticmethod
    def img(li):
        # 商品图片地址
        img_src = li.select_one("div[class=z-feed-img] a img").get("src", "")
        if img_src.startswith("//"):
            img_src = "https:" + img_src
        else:
            # TODO: gift
            img_src = ""

        return _session.get(img_src, headers=HEADERS).content
    
    @staticmethod
    def cid():
        return make_msgid()[1:-1]

    @error_handler
    def _generate(self, li):
        cid = self.cid()
        img = self.img(li)
        data = self.data(li)
        tmpl = self._template.format(**{
            "cid": cid,
            # 商品名
            "name": data.get("ecommerce", {}).get("add", {}) \
                .get("products", [{}])[0].get("name", "暂无").strip(),
            # 商品价格
            "price": data.get("ecommerce", {}).get("add", {}) \
                .get("products", [{}])[0].get("price", "暂无"),
            # 商品所属购物平台
            "grocery": data.get("ecommerce", {}).get("add", {}) \
                .get("products", [{}])[0].get("dimension12", "暂无").strip(),
            "link": self.link(li),
            "publish": self.publish(li),
        })
        self.message.add_alternative(tmpl, subtype="html")
        self.message.get_payload()[-1].add_related(img, "image", "png", cid=cid)

    def generate(self):
        for li in self.lis(): 
            if self.channel(li) in TARGET["channels"]:
                self._generate(li)
        return self.message


class Handler:

    def __init__(self, search, interval):
        self.state = ""
        self.search = search
        self.interval = interval
        self.scheduler = scheduler()
        self.server = smtplib.SMTP_SSL(CONFIG["server_addr"],
                                       CONFIG["server_port"])

    def _get_html(self):
        url = TARGET["url"].format(self.search)
        return _session.get(url, headers=HEADERS).text

    def _get_message(self):
        html = self._get_html()
        et = EmailTemplate(html)
        return et.generate()

    def send_email(self):
        self.server.connect(CONFIG["server_addr"], CONFIG["server_port"])
        self.server.login(CONFIG["sender"], CONFIG["server_passwd"])
        # self.server.set_debuglevel(1)     # for debug
        self.server.send_message(self._get_message())
        self.server.quit()

    def callback(self):
        self.scheduler.enter(self.interval, 1, self)
        self.scheduler.run()

    def __call__(self):
        if self.state == "cancel":
            return 
        self.send_email()
        self.callback()
