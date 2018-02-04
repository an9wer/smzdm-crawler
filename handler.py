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

try:
    from config import EMAIL
except ImportError:
    EMAIL = {
        "server": (input("smtp server: "), input("smtp server port: ")),
        "passwd": input("smtp server passwd: "),
        "sender": input("email sender: "),
        "receivers": input("email receivers (split by comma): ").split(","),
        "subject": input("email subject: "),
        "template": "<h3>{name}({grocery})</h3>"
                    "<div><a href='{link}'><img src='cid:{cid}'></a></div>"
                    "<div><p>价格：￥{price}; 发布日期：{publish}</p></div>"
                    "<hr>",
    }


REQUESTS = {
    "target": "https://search.smzdm.com/?c=home&s={}".format(input("keyword: ")),
    "headers": {
        "referer": "https://www.smzdm.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/63.0.3239.132 Safari/537.36",
    }
}

PAGE = {
    "tags": ["国内优惠", "海淘优惠", "发现优惠"],
    "nexts": ["去购买"],
    "gift": "https://timgsa.baidu.com/timg?image&quality=80&size=b9999_10000&"
            "sec=1517327637564&di=04f86f0568f35d122026db50b41f6561&imgtype=0&"
            "src=http%3A%2F%2Fimg5.duitang.com%2Fuploads%2Fitem%2F201601%2F25"
            "%2F20160125210516_t3nKj.jpeg",
}


class Handler:

    def __init__(self):
        self.session = requests.Session()
        #self.soup = BeautifulSoup(html, "html.parser")

        self.message = EmailMessage()
        self.message["From"] = EMAIL["sender"]
        self.message["To"] = ",".join(EMAIL["receivers"])
        self.message["Subject"] = EMAIL["subject"]

        self.server = smtplib.SMTP_SSL(*EMAIL["server"])

    def get_page(self):
        r = self.session.get(REQUESTS["target"], headers=REQUESTS["headers"])
        return r.text

    def get_msg(self, html):
        assert isinstance(html, str)
        self.soup = BeautifulSoup(html, "html.parser")

        lis = self.soup.select("ul[id=feed-main-list] li")
        for li in lis:
            # tag 标签
            tag = li.select_one("div[class=z-feed-img] span").string
            if tag not in PAGE["tags"]:
                continue

            # 去购买 标签
            a = li.select_one("div[class=feed-link-btn-inner] a")
            if a.contents[0] not in PAGE["nexts"]:
                continue

            data = re.findall(r"push\((.*?)\)", a["onclick"])[1]
            if data is None:
                continue

            try:
                data = json.loads(data.replace("'", '"'))
            except Exception:
                continue
            # 商品名
            name = data.get("ecommerce", {}).get("add", {}) \
                   .get("products", [{}])[0].get("name", "暂无").strip()
            # 价格
            price = data.get("ecommerce", {}).get("add", {}) \
                    .get("products", [{}])[0].get("price", "暂无")
            # 商城
            grocery = data.get("ecommerce", {}).get("add", {}) \
                      .get("products", [{}])[0].get("dimension12", "暂无").strip()

            # 链接
            # link = a.get("href", "").strip()  # 在商城中的链接
            link = li.select_one("div[class=z-feed-img] a").get("href", "").strip()
            # 发布日期
            publish = li.select_one("span[class=feed-block-extras]").contents[0].strip()
            # 图片
            img_src = li.select_one("div[class=z-feed-img] a img").get("src")
            if img_src:
                if img_src.startswith("//"):
                    img_src = "https:" + img_src
            else:
                img_src = PAGE["gift"]
            img = self.session.get(img_src, headers=REQUESTS["headers"]).content

            cid = make_msgid()
            self.message.add_alternative(
                EMAIL["template"].format(
                    name=name, grocery=grocery, price=price,
                    publish=publish, link=link, cid=cid[1:-1],
                ),
                subtype="html",
            )
            self.message.get_payload()[-1].add_related(img, "image", "png", cid=cid)

    def send_email(self):
        self.server.login(EMAIL["sender"], EMAIL["passwd"])
        self.server.send_message(self.message)
        self.server.quit()

    def __call__(self):
        html = self.get_page()
        self.get_msg(html)
        self.send_email()

if __name__ == "__main__":
    Handler()()
    print("Done!")
