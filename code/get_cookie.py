#!/usr/bin/env python
# -*- coding: UTF-8 -*-


from selenium import webdriver
import time


def parse_cookie(browser, platform):
    tag = True
    while tag:
        cookie = browser.get_cookies()
        for item in cookie:
            if platform == 'jd' and item.get('name', '') == 'shshshsID':
                tag = False
                break
            if platform == 'taobao' and item.get('name', '') == 'lgc':
                tag = False
                break
        time.sleep(3)

    cookie = browser.get_cookies()
    # print(cookie)
    browser.close()
    ret = ''
    for item in cookie:
        ret = ret + item['name'] + '=' + item['value'] + '; '
    # print(ret.strip('; '))
    return ret.strip('; ')


def run(platform):
    # 启动谷歌浏览器
    browser = webdriver.Chrome('chromedriver.exe')
    # 设置窗口最大化
    browser.maximize_window()

    if platform == 'taobao':
        url = 'https://login.taobao.com/member/login.jhtml?redirectURL=https%3A%2F%2Fwww.taobao.com%2F'
        browser.get(url)
        cookie = parse_cookie(browser, platform)
    else:
        url = 'https://passport.jd.com/new/login.aspx?ReturnUrl=https%3A%2F%2Fwww.jd.com%2F'
        browser.get(url)
        cookie = parse_cookie(browser, platform)
    return cookie


if __name__ == '__main__':
    platform = 'taobao'
    run(platform)
