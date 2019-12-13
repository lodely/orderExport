#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# @File : error_check.py


import jd_orders
import taobao_orders
import get_cookie
import db_common
import time
import os


def check_jd(jd_list):
    # 设置cookie
    cookie = get_cookie.run('jd')
    cookie = cookie.replace('\n', '')
    spider = jd_orders.Spider()
    spider.set_cookie(cookie)
    file_path = './jd_error'
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    for url in jd_list:
        html = spider.get_html(url)
        order_id = db_common.fj_function(url, 'orderid=', '&')[1]
        file_name = '/order_{}.txt'.format(order_id)
        with open(file_path+file_name, 'w') as f:
            f.write(html)


def check_taobao(taobao_list):
    # 设置cookie
    cookie = get_cookie.run('taobao')
    cookie = cookie.replace('\n', '')
    spider = taobao_orders.Spider()
    spider.set_cookie(cookie)
    file_path = './taobao_error'
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    for page in taobao_list:
        html = spider.get_html(page)
        file_name = '/page_{}.txt'.format(page)
        with open(file_path+file_name, 'w') as f:
            f.write(html)


def main():
    jd_list = []
    taobao_list = []
    try:
        with open('test_config.txt', 'r') as f:
            config_data = f.read()
            jd_list = db_common.GetJsonValue(config_data, 'jd')
            taobao_list = db_common.GetJsonValue(config_data, 'taobao')
    except Exception:
        pass
    if jd_list:
        check_jd(jd_list)
        time.sleep(5)
    if taobao_list:
        check_taobao(taobao_list)


if __name__ == '__main__':
    main()
