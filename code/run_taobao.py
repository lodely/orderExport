#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import taobao_orders
import get_cookie


def main():
    try:
        print_data = '请勿关闭该窗口，订单导出结束后会自动关闭！！'
        print(print_data.decode('utf-8').encode('gbk'))
        # 设置cookie
        cookie = get_cookie.run('taobao')
        taobao_orders.main(cookie)
    except Exception as e:
        print(e)
    print('ok')

if __name__ == '__main__':
    main()
