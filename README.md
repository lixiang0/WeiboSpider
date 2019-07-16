# weibo

通过手动收集微博上的资料比较繁琐。

本项目只需要执行'''scrapy crawl weibo'''即可将微博上的微博或文章下载到本地，方便进行整理。

# 安装scrapy

'''pip install scrapy'''

# 安装bs4

'''pip install beautifulsoup4'''

# 执行

在项目根目录weibo执行：
'''scrapy crawl weibo'''爬取微博

或者
'''python spiders/wenzhang.py'''爬取文章

# TIPs

在执行前需要获取cookie，具体做法为，打开浏览器https://weibo.cn进行登录。
登陆成功之后在浏览器界面按下F12-->选择network-->weibo.cn-->找到cookie，如下图：
![](./weibo.png)

然后需要把对应的值填入：
1.'''spiders/weibo.py'''如下代码段中：
'''
    cookie = {'_T_WM':'',
            'ALF':'',
             'SCF':'-.',
             'SUB':'',
             'SUBP':'',
             'SUHB':'',
             'SSOLoginState':''}  # 将cookie替换成自己的cookie
'''

2.'''spiders/wenzhang.py'''下直接将拷贝到的cookie粘贴到下面代码段：
'''
cookie = {'Cookie': ''}  # 将cookie替换成自己的cookie
'''

