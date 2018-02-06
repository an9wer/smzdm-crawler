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

from config import HandlerConfig


_session = requests.session()
_config = HandlerConfig()

_headers = {
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
            #print(222)
            try: return self.func(ins, *args, **kwargs)
            except Exception: print(111)
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
        self.message["From"] = _config["email.sender"]
        self.message["To"] = ",".join(_config["email.receivers"])
        self.message["Subject"] = _config["email.subject"]

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
        #a = li.select_one("div[class=feed-link-btn-inner] a")
        #data = re.findall(r"push\((.*?)\)", a["onclick"])[1]
        go_buy = li.select_one("div[class=feed-link-btn-inner] a")
        #print(go_buy["onclick"])
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

        return _session.get(img_src, headers=_headers).content
    
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
            if self.channel(li) in _config["target.channels"]:
                self._generate(li)
        return self.message


class Handler:

    def __init__(self):
        print(_config)
        self.server = smtplib.SMTP_SSL(_config["email.server_addr"],
                                       _config["email.server_port"])

    @staticmethod
    def _get_html():
        return _session.get(_config["target.url"], headers=_headers).text

    def _get_message(self):
        html = self._get_html()
        et = EmailTemplate(html)
        return et.generate()

    def send_email(self):
        self.server.login(_config["email.sender"],
                          _config["email.server_passwd"])
        self.server.send_message(self._get_message())
        self.server.quit()


if __name__ == "__main__":
    hd = Handler()
    hd.send_email()
    print("Done!")
