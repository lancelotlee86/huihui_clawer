# encoding=utf8
# !/usr/bin/python3

import datetime
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import threading
from pymongo import  MongoClient
from models import Item
try:
    import config_instance
except ImportError:
    import config

# setup mongodb
client = MongoClient()
db = client.shopping_clawer
huihui = db.huihui_clawer


def send_email(items_to_email):
    """
    一个辅助方法，接收一个Item对象的列表，并提取我们需要的数据，格式化后发送邮件出去
    :param items_to_email: 装着Item对象的列表
    :return: None
    """
    print("sending email..." + str(datetime.datetime.now()))
    sender = config_instance.SENDER
    receiver = config_instance.RECEIVER
    subject = config_instance.SUBJECT
    smtpserver = config_instance.SMTPSERVER
    username = config_instance.USERNAME
    password = config_instance.PASSWORD

    body = ''
    count = 1
    for item in items_to_email:
        text = '{}. ({})  {} {}\n'.format(count, item.date,item.title, item.link)
        body = body + text
        count += 1

    msg = MIMEText(body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = sender
    msg['To'] = receiver

    smtp = smtplib.SMTP()
    smtp.connect(smtpserver)
    smtp.login(username, password)
    smtp.sendmail(sender, [receiver], msg.as_string())
    smtp.quit()


class Clawer:
    headers = None
    url = None
    reponse = None


class HuihuiClawer(Clawer):
    """
    慧慧网不需要模拟访问页面，直接访问API就行
    """
    def __init__(self):
        self.headers = {
            'Host': 'www.huihui.cn',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2794.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Cookie': 'OUTFOX_SEARCH_USER_ID=-2090932312@222.137.30.190; fvf_gouwu=http://zhushou.huihui.cn/installed?browser=chrome&version=4.2.9.6&vendor=chromenew; fvt_gouwu=2016-06-21; vts_gouwu=1; showFriendTip=1; HUIHUI_SESS=SGcoFzosfdzhs99NqeiT6gAAAABYcPKc; huihui_actid=-1434015657; sf_gouwu=https://www.baidu.com/link?url=i77yiJ83S2rQIrpMBLpZlzRoableu7mv4GDNeDxojkm&wd=&eqid=bcfcb67e0007d48300000003578630e3; vendor_gouwu=baidu.com; vts_gouwu=520; HUIHUI_LOGINED=true',
            'DNT': '1'
        }

        self.url = 'http://www.huihui.cn/recommenddeal/data.json?domain=all&page=1&maxId=0&pagebar=1&sort=0&_=1468421029126'

    def open_url(self, url=None):
        """
        打开给定或默认的URL，用Requests库请求
        :param url: str
        :return: requests的响应对象
        """
        if url:
            self.url = url
        # 试着访问，如果超时或者别的原因，则返回空
        try:
            r = requests.get(url=self.url, headers=self.headers, timeout=2)
            if r.status_code != 200:
                return None
        except:
            return None
        print('request sent')
        r.encoding = 'utf-8'
        return r

    @staticmethod
    def close_response(response):
        response.close()

    @staticmethod
    def parase(response):
        """
        得到返回的JSON对象
        :return: items
        """
        data = response.json()
        return data

    @staticmethod
    def get_items(data):
        """
        接收 parase() 方法传递的 JSON 对象，得到包含着Item对象的列表
        :param soup: JSON 对象
        :return: 包含着Item对象的列表
        """
        all_items = data['data']   # 获取包含着所有物品的列表

        # 其实下面的步骤不需要，直接把all_items返回就行，字典列表
        # 但是为了拓展性和可操作性，还是重新将需要的数据封装成对象吧
        items = []      # 一个装着Item对象的列表
        for item in all_items:  # 循环中，每一个item都代表一个item所在的div标签
            this_item = Item()  # 实例化一个新的Item对象

            this_item.link = 'http://www.huihui.cn' + item['url']  # 获取链接
            this_item.title = item['title']  # 获取这个商品的标题
            this_item.price = item['price']  # 获取这个商品的价格
            this_item.date = item['timestamp']      # 时间

            items.append(this_item)     # 添加当前的Item对象到items列表
        return items

    @staticmethod
    def exist(item):
        """
        检查给定的item是否存在在数据库中
        :param item: Item对象
        :return: Boolean
        """
        if huihui.find_one({'link': item.link}):     # 没有文章id，那么就判断链接吧
            return True     # 如果该记录已存在
        else:
            return False


def main():
    """
    main()做一下几个事，
    1. 2秒后开启新的Threading运行main()---->>
    2. 访问api接口得到这一时间点的所有页面上的items---->>
    3. 遍历items，不在数据库中的，添加到数据库，并且添加到items_to_mail[]---->>
    4. 调用send_email()将items_to_mail[]发送出去
    :return: None
    """
    threading.Timer(60, main).start()    # 每次开始main函数时，新开一个递归的线程，以此实现每60秒请求一次
    now = datetime.datetime.now()
    print('starting a new threading: ' + str(threading.current_thread().ident) + ' @ ' + str(now))
    print('total threads alive count: ' + str(threading.active_count()))

    # 下面4行做的工作：访问页面-->解析页面-->得到item对象的列表
    huihui_clawer = HuihuiClawer()
    response_page = huihui_clawer.open_url()
    if not response_page:   # 如果返回的页面是None，则跳过这一轮请求
        print('页面请求失败...')
        return
    parsed_page = huihui_clawer.parase(response_page)
    items_in_huihui = huihui_clawer.get_items(parsed_page)  # 得到了所有的item对象，在一个列表item_in_smzdm中
    huihui_clawer.close_response(response_page)

    # 检查页面中每一条记录是否已存在，如不存在，说明是新的记录，通过邮件发送并存储在数据库中
    items_to_email = []
    for item in items_in_huihui:
        if not HuihuiClawer.exist(item):  # 记录没有在数据库中
            items_to_email.append(item)  # 将这条记录添加到待邮列表中
            print('new item found, sending email...')
            print(item.to_dict())
            huihui.insert_one(item.to_dict())  # 将这条记录存放在数据库中
    if items_to_email:  # 将这次请求找到的items发送出去
        send_email(items_to_email)

    print('after process threading' + str(threading.current_thread().ident))
    return

if __name__ == '__main__':
    main()
