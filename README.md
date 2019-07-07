# weibo
平时生活喜欢用微博转发一些大牛的研究成果，但是每次整理非常的麻烦。

所以就萌生一个想法：能不能自动将转发过的微博下载到本地，这样就免去了很多麻烦？

本项目只需要执行```scrapy crawl weibo```即可将微博上转发的微博下载到本地，方便进行整理。

# 安装scrapy

```pip install scrapy```

# 执行

项目根目录执行：

```scrapy crawl weibo```

#TIP

在执行前需要获取cookie，具体做法为，打开浏览器https://weibo.cn进行登录。
登陆成功之后在浏览器界面按下F12-->选择network-->weibo.cn-->找到cookie，如下图：
![](./weibo.png)
然后需要把对应的值填入```spiders/weibo.py```如下代码段中：

```
    cookie = {'_T_WM':'',
            'ALF':'',
             'SCF':'-.',
             'SUB':'',
             'SUBP':'',
             'SUHB':'',
             'SSOLoginState':''}  # 将cookie替换成自己的cookie
```
