双11剁手之后，想看看到底花了多少钱，发现某宝和某东竟然不能导出购物记录，自己动手做了小程序，可以直接导出csv文件，共享给大家，可以看看自己花了多少钱。

自己做着玩的，偶尔运行会出错，可以多运行几次。执行后，在程序文件夹生成了csv文件，就是导出成功了。如果没有生成，就在执行一次看看。

关于安全性的问题，其实就是一个本地的浏览器打开页面，生成的数据也在本地，自己看而已。
# 打包成exe
安装`pyinstaller`，运行：
```
pyinstaller.exe -F D:\Desktop\code\run_jd.py -p D:\Desktop\code\get_cookie.py -p D:\Desktop\code\jd_orders.py -p D:\Desktop\code\db_common.py --hidden-import get_cookie --hidden-import jd_orders --hidden-import db_common
```

# 更新
2019-12-23：
1、增加一个64位版本，解决了运行过程中浏览器崩溃的问题；
2、电脑64位系统则使用64位版本（5年内的电脑基本都是64位系统），32位系统则使用32位版本；
3、删除了可能引起杀毒软件误报的部分内容。