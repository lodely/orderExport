#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# @File : taobao_orders.py


from functools import wraps
import requests
import sys
import db_common
import csv
import codecs
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
                self.param['spider_start_time'] = db_common.GetJsonValue(config_data, 'taobao', 'spider_start_time')
                if not self.param['spider_start_time']:
                    self.param['spider_start_time'] = '2019-07-01'
        except Exception:
            self.param['spider_start_time'] = '2019-07-01'

    def set_cookie(self, cookie):
        self.cookie = cookie

    def get_html(self, page='1'):
        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'content-length': '33',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': self.cookie,
            'origin': 'https://buyertrade.taobao.com',
            'referer': 'https://buyertrade.taobao.com/trade/itemlist/list_bought_items.htm?spm=a21bo.2017.1997525045.2.5af911d93UiX05',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        param = {
            'pageNum': page,
            'pageSize': '15',
            'prePageNo': '1'
        }
        url = 'https://buyertrade.taobao.com/trade/itemlist/asyncBought.htm?action=itemlist/BoughtQueryAction&event_submit_do_query=1&_input_charset=utf8'
        html = requests.post(url, headers=headers, data=param).text
        return html

    @staticmethod
    def get_total_page(html):
        total_page = db_common.GetJsonValue(html, 'page', 'totalPage')
        return total_page

    def parse_orders_item(self, obj_date, item):
        url = db_common.fj_function(item, "href='//", "'")[1]
        orders_date = db_common.fj_function(item, '<span class="dealtime" title="', '">')[1]
        if orders_date[:10] < obj_date:
            self.end_tag = True
        return [url, orders_date]

    def parse_list(self, html):
        items = db_common.GetJsonValue(html, 'mainOrders')
        ret = []
        for item in items:
            order_result = self.parse_detail(item)
            if self.end_tag:
                break
            ret += order_result
        return ret

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
            goods_ret.append([order_id, dates] + goods)
        for amount in amounts:
            amounts_ret.append([order_id] + amount)
        return goods_ret, amounts_ret

    def get_status(self, item):
        status = db_common.GetJsonValue(item, 'statusInfo', 'text')
        if status == '订单详情':
            step_list = db_common.GetJsonValue(item, 'stepPayList')
            for step in step_list:
                current = db_common.GetJsonValue(step, 'current')
                if current:
                    status = db_common.GetJsonValue(step, 'status', 'text')
        return status

    def parse_detail(self, item):
        order_result = []
        order_time = db_common.GetJsonValue(item, 'orderInfo', 'createDay')  # 订单创建时间
        order_id = db_common.GetJsonValue(item, 'id')
        actual_pay = db_common.GetJsonValue(item, 'payInfo', 'actualFee')  # 实付款
        status = self.get_status(item)
        shop_name = db_common.GetJsonValue(item, 'seller', 'shopName')
        shop_url = db_common.GetJsonValue(item, 'seller', 'shopUrl')
        for prod_info in db_common.GetJsonValue(item, 'subOrders'):
            item_info = prod_info['itemInfo']
            item_id = item_info.get('id', '')
            if item_id:
                url = 'https:' + prod_info['itemInfo']['itemUrl']
                title = prod_info['itemInfo']['title']
                item_price = prod_info['priceInfo']['realTotal']
                item_count = prod_info['quantity']
                if order_time < self.param['spider_start_time']:
                    self.end_tag = True
                    break
                order_result.append(['"'+order_id+'"', order_time, shop_name, shop_url, title, url, status, item_count,
                                     item_price, actual_pay])
        return order_result

    def order_list(self):
        html = self.get_html('1')
        total_page = self.get_total_page(html)
        olt = self.parse_list(html)
        page = 2
        while not self.end_tag and page < total_page+1:
            html = self.get_html(str(page))
            olt += self.parse_list(html)
            page += 1
        return olt


def main(cookie):
    cookie = cookie.replace('\n', '')
    spider = Spider()
    spider.set_cookie(cookie)
    orders_ret = spider.order_list()

    if orders_ret:
        column_name = [
            "订单号", "订单日期", "店铺名", "店铺链接", "商品名", "链接", "订单状态", "商品数量", "商品单价", "订单实付款"
        ]
        with codecs.open(u'淘宝(天猫)订单列表.csv', 'w', 'gbk') as f:
            writer = csv.writer(f)
            writer.writerow(column_name)
            for item in orders_ret:
                writer.writerow(item)


if __name__ == '__main__':
    # 设置cookie
    cookies = ""
    main(cookies)
