#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# @File : jd_orders.py


from functools import wraps
import requests
import re
import sys
import db_common
import csv
import codecs
import datetime
reload(sys)
sys.setdefaultencoding('utf-8')


def debug(func):
    @wraps(func)
    def wrapper(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception as e:
            print('[Function name]: ' + func.__name__)
            print('[Error info]: ' + str(e))
    return wrapper


class Spider:
    def __init__(self):
        self.end_tag = False
        self.cookie = ''
        self.param = dict()
        self.read_config()

    def read_config(self):
        try:
            with open('config.txt', 'r') as f:
                config_data = f.read()
            self.param['spider_start_time'] = db_common.GetJsonValue(config_data, 'jd', 'spider_start_time')
            if len(self.param['spider_start_time']) < 10:
                items = self.param['spider_start_time'].split('-')
                temp = items[0]
                for item in items[1:]:
                    temp = '{}-0{}'.format(temp, item) if len(item) < 2 else '{}-{}'.format(temp, item)
                self.param['spider_start_time'] = temp
            self.param['orders_year'] = self.param['spider_start_time'][:4]
            self.param['diff'] = int(datetime.datetime.now().strftime('%Y')) - int(self.param['orders_year'])
            if not self.param['spider_start_time']:
                self.param['spider_start_time'] = '2019-07-01'
                self.param['orders_year'] = self.param['spider_start_time'][:4]
        except Exception:
            self.param['spider_start_time'] = '2019-07-01'
            self.param['orders_year'] = self.param['spider_start_time'][:4]
            self.param['diff'] = 0

    def set_cookie(self, cookie):
        self.cookie = cookie

    def get_html(self, url, method='get'):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
                      'q=0.8,application/signed-exchange;v=b3',
            # 'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
            'cache-control': 'max-age=0',
            'cookie': self.cookie,
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-site',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/77.0.3865.90 Safari/537.36'
        }
        if method == 'post':
            data = {'popVenderIds': self.param['vender_id']}
            html = requests.post(url, data=data, headers=headers).text
        else:
            html = requests.get(url, headers=headers).text
        try:
            html = html.encode('utf-8')
        except Exception as e:
            print(e)
        return html

    def get_total_page(self, html):
        total_page = 200
        # try:
            # pattern = re.compile(r'共(\d+)页')
            # content = re.search(pattern, html).group(1)
            # if content:
            #     total_page = int(content)
        # except:
        #     self.end_tag = True
        return total_page

    def construct_url(self, tag):
        url = ''
        if tag == 'list':
            # 订单列表api，抓今年来d=2，最近三个月d=0，2019为当年
            url = 'https://order.jd.com/center/list.action?d=' + self.param['orders_year'] + '&s=4096&page={}'
        elif tag == 'detail':
            # url = 'https://details.jd.com/normal/item.action?orderid=&PassKey='
            url = ''
        elif tag == 'shop':
            # 店铺信息api
            url = 'https://details.jd.com/lazy/getPopTelInfo.action'
        elif tag == 'presale':
            # 预售订单价格api
            url = 'https://yuding.jd.com/ordersoa/presale/orderdetail?callback=jQuery1831713&orderid={0}&y={1}&key={2}&_=1576203059501'
        return url

    def parse_orders_item(self, item):
        url = db_common.fj_function(item, "href='//", "'")[1]
        if not url:
            url = db_common.fj_function(item, 'href="//', '"')[1]
        if not url:
            url = db_common.fj_function(item, "href='", "'")[1].replace('http://', '').replace('https://', '')
        orders_date = db_common.fj_function(item, '<span class="dealtime" title="', '">')[1]
        if orders_date[:10] < self.param['spider_start_time']:
            self.end_tag = True
        return [url, orders_date]

    def parse_list(self, html):
        url_list = []
        data = []
        items = html.split('<tr class="sep-row"><td colspan="5"></td></tr>')
        for item in items[1:]:
            if item.count('<tr class="tr-th tr-th-02">'):
                inside_items = item.split('<tr class="tr-th tr-th-02">')
                for i_item in inside_items[1:]:
                    i_data = self.parse_orders_item(i_item)
                    if self.end_tag:
                        break
                    url_list.append(i_data)
            else:
                data = self.parse_orders_item(item)
            if self.end_tag:
                break
            if data:
                url_list.append(data)
                data = []
        return url_list

    def get_shop_info(self, html):
        shop_data = db_common.fj_function(html, '<div class="mt goods-head">', '</div>')[1]
        shop_name = db_common.fj_function(shop_data, '<span class="shop-name">', '</span>')[1]
        shop_url = ''
        if not shop_name:
            self.param['vender_id'] = db_common.fj_function(html, 'id="venderIdListStr" value="', '"')[1]
            url = self.construct_url('shop')
            req_shop = self.get_html(url, 'post')
            shop_name = db_common.fj_function(req_shop, '"venderName":"', '"')[1]
            shop_url = db_common.fj_function(req_shop, '"venderUrl":"', '"')[1]
        return shop_name, shop_url

    @staticmethod
    def get_brand(ware_info, pid):
        brand_id = ''
        cate = ''
        try:
            ware_info = eval(ware_info)
        except Exception:
            ware_info = []
        for ware in ware_info:
            sku_id = int(db_common.GetJsonValue(ware, 'skuId'))
            if sku_id == int(pid):
                brand_id = db_common.GetJsonValue(ware, 'brandId')
                cate = db_common.GetJsonValue(ware, 'classify')
                break
        return brand_id, cate

    @staticmethod
    def get_real_pay(html):
        pay_money = db_common.fj_function(html, '<span class="txt count">', '</span>'
                                          )[1].replace('&yen;', '').replace('￥', '')
        if not pay_money:
            temp = db_common.fj_function(html, '应付总额', '</div>')[1]
            pay_money = db_common.fj_function(temp, ';', '</span>')[1].replace('\n', '').strip()
        return pay_money

    def get_goods_price(self, title, html, f_price):
        # 获取正常价格
        pattern = re.compile(r'(\d+\.\d+)')
        price_data = re.search(pattern, f_price)
        # 检查是否预售订单
        presale = db_common.fj_function(html, '<span id="yuShouOrderItemJson" style="display:none;">', '</span>')[1]
        if title.count('赠品') or title.count('非卖品') or title.count('请勿'):
            price = "赠品"
        elif price_data:
            price = price_data.group()
        elif presale:
            order_id = db_common.GetJsonValue(presale, 'orderid')
            yn = db_common.GetJsonValue(presale, 'yn')
            passkey = db_common.GetJsonValue(presale, 'passkey')
            url = self.construct_url('presale').format(order_id, yn, passkey)
            p_html = self.get_html(url)
            price = db_common.fj_function(p_html, '"yPrice":"', '"')[1]
        elif f_price.count('赠品'):
            price = "赠品"
        else:
            price = "0"
        return price

    def goods_info(self, html):
        shop_name, shop_url = self.get_shop_info(html)
        items = db_common.fj_function(html, '<table class="tb-void tb-order">', '<tr class="J-yunfeixian"'
                                      )[1].split('<div class="p-item"')
        status = db_common.fj_function(html, '<h3 class="state-txt ftx-02">', '</h3>')[1]
        if not status:
            status = db_common.fj_function(html, "<h3 class='state-txt ftx-02'>", '</h3>')[1]
        pay_money = self.get_real_pay(html)
        ware_info = db_common.fj_function(html, "['fwjBuyInWareInfo']='", "';")[1]
        # 临时添加，收件人信息
        # tmp = db_common.fj_function(html, '收货人：', '</div>')[1]
        # user_name = re.sub('<.*?>', '', tmp).strip()
        # tmp = db_common.fj_function(html, '地址：', '</div>')[1]
        # address = re.sub('<.*?>', '', tmp).strip()
        # tmp = db_common.fj_function(html, '手机号码：', '</div>')[1]
        # phone = re.sub('<.*?>', '', tmp).strip()

        goods_list = []
        for item in items[1:]:
            url = db_common.fj_function(item, '<a href="//', '"')[1]
            temp = db_common.fj_function(item, '<div class="p-name">', '</div>')[1].replace('\t', '').replace('\n', '')
            title = re.sub('<.*?>', '', temp).strip()
            pid = db_common.fj_function(item, 'id="coupon_', '"')[1]
            brand_id, cate = self.get_brand(ware_info, pid)
            f_price = db_common.fj_function(item, '<span class="f-price', '</span>')[1]
            price = self.get_goods_price(title, html, f_price)
            temp = db_common.fj_function(item, '<span class="f-price', '<td id="jingdou')[1]
            count = db_common.fj_function(temp, '<td>', '</td>')[1]
            goods_list.append([shop_name, shop_url, title, url, status, count, price,
                               pay_money, brand_id, cate])
        return goods_list

    @staticmethod
    def money(html):
        items = db_common.fj_function(html, '<div class="goods-total">', '</div>')[1].split('<span class="labe')
        amounts = []
        for item in items[1:]:
            name = db_common.fj_function(item, 'l">', '：</span>')[1].replace('　', '')
            txt = db_common.fj_function(item, '&yen;', '</span>')[1].replace('\n', '').replace(' ', '')
            amounts.append([name, txt])
        return amounts

    @staticmethod
    def format_ret(order_id, dates, goods_list, amounts):
        goods_ret, amounts_ret = [], []
        for goods in goods_list:
            goods_ret.append(['"'+order_id+'"', dates] + goods)
        for amount in amounts:
            amounts_ret.append([order_id] + amount)
        return goods_ret, amounts_ret

    def get_global_brand(self, url):
        html = self.get_html('https://' + url)
        brand_id = db_common.fj_function(html, 'brand: ', ',')[1]
        cate = db_common.fj_function(html, 'cat: [', ']')[1].replace(',', ';')
        return brand_id, cate

    def get_global_user(self, html):
        # 收件人信息
        users = db_common.fj_function(html, '<div class="user-info">', '商品信息')[1]
        items = users.split('<div class="row">')
        user_name = address = phone = ''
        for item in items:
            if item.count('收货人信息'):
                tmp = db_common.fj_function(item, '<div class="txt"', '</div>')[1]
                tmp = re.sub('<.*?>', '', tmp).strip()
                user_name = db_common.fj_function(tmp, '>', '（')[1]
                phone = db_common.fj_function(tmp, '（', '）')[1]
            elif item.count('收货地址'):
                tmp = db_common.fj_function(item, '<div class="txt">', '</div>')[1]
                address = re.sub('<.*?>', '', tmp).strip()
        return user_name, address, phone

    def global_goods_info(self, html):
        goods_list = []
        shop_data = db_common.fj_function(html, '店铺名称：', '联系卖家')[1]
        shop_name = db_common.fj_function(shop_data, '<span>', '</span>')[1]
        shop_url = ''
        pay_money = db_common.fj_function(html, '<b class="red">¥', '</b>')[1]
        status = db_common.fj_function(html, '当前状态：', '</div>')[1]
        # user_name, address, phone = self.get_global_user(html)

        temp = db_common.fj_function(html, '<td class="itemName">', '<div class="price-info presale-price-info">')[1]
        items = temp.split('<tr class="tr-td" skuid')
        for item in items[1:]:
            temp = db_common.fj_function(item, '<div class="p-msg">', '<div class="p-msg">')[1]
            title = db_common.fj_function(temp, 'target="_blank">', '</a>')[1]
            url = db_common.fj_function(temp, '<a href="//', '"')[1]
            count = db_common.fj_function(item, '<td class="num">', '</td>')[1]
            price = db_common.fj_function(
                item, '<td class="jdPrice">', '</td>')[1].replace('¥', '').replace('\n', '').strip()
            brand_id, cate = self.get_global_brand(url)
            goods_list.append([shop_name, shop_url, title, url, status, count, price,
                               pay_money, brand_id, cate])
        return goods_list

    def parse_detail(self, html, orders_date):
        order_id = db_common.fj_function(html, '订单号：', '</div>')[1]
        if not order_id and html.count('我的京东国际订单'):
            order_id = db_common.fj_function(html, '<li class="active">订单', '</li>')[1]
            goods_list = self.global_goods_info(html)
        else:
            goods_list = self.goods_info(html)
        amounts = self.money(html)
        goods_ret, amounts_ret = self.format_ret(order_id, orders_date, goods_list, amounts)
        return goods_ret

    def order_list(self):
        olt = []
        url = ''
        while self.param['diff'] >= 0:
            try:
                url = self.construct_url('list').format('1')
                html = self.get_html(url)
                total_page = self.get_total_page(html)
                if not self.end_tag:
                    olt += self.parse_list(html)
                page = 2
                while not self.end_tag and page < total_page+1:
                    url = self.construct_url('list').format(page)
                    html = self.get_html(url)
                    if html.count('最近没有下过订单哦'):
                        break
                    olt += self.parse_list(html)
                    page += 1
                self.end_tag = False
                self.param['diff'] -= 1
                self.param['orders_year'] = str(int(self.param['orders_year']) + 1)
            except Exception as e:
                error_str = '''
                    url: {}
                    order_list error: {}
                '''.format(url, e)
                print(error_str)
        return olt


def main(cookie):
    cookie = cookie.replace('\n', '')
    spider = Spider()
    spider.set_cookie(cookie)
    olt = spider.order_list()
    orders_ret = []
    url = ''
    for item in olt:
        try:
            url = item[0]
            orders_date = item[1]
            detail_html = spider.get_html('https://' + url)
            goods_ret = spider.parse_detail(detail_html, orders_date)
            if goods_ret:
                orders_ret += goods_ret
        except Exception as e:
            error_str = '''
                url: {}
                parse_detail error: {}
            '''.format(url, e)
            print(error_str)
    if orders_ret:
        column_name = [
            "订单号", "订单日期", "店铺名", "店铺链接", "商品名", "链接", "订单状态",
            "商品数量", "商品单价", "订单实付款", "品牌", "类别"
        ]
        with codecs.open(u'京东订单列表.csv', 'w', 'gbk') as f:
            writer = csv.writer(f)
            writer.writerow(column_name)
            for item in orders_ret:
                writer.writerow(item)
    else:
        with codecs.open(u'京东--该账号没有订单数据，请检查.csv', 'w', 'gbk') as f:
            f.write('')


if __name__ == '__main__':
    # 设置京东cookie
    cookies = ""
    main(cookies)
