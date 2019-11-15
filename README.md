# 微博爬虫

+ [0.项目介绍](##0.项目介绍)

+ [1.项目特色](##1.项目特色)

+ [2.项目部署（ubuntu）](##2.项目部署（ubuntu）)

+ [3.PC端预览](##3.PC端预览)

+ [4.手机端预览](##4.手机端预览)


## 0.项目介绍

一个本地的微博，用于学习前端、后台、爬虫方面的技术。

实际部署效果：[参考连接](http://weibo.rubenxiao.com),网址打不开的话点击[参考连接](http://122.51.50.206:8088)

截图参考本页末尾。。


## 1.项目特色

#### 1.1 项目出发点在于构建一个属于自己的本地微博系统，并规避微博APP上越来越多植发广告的骚扰；

#### 1.2 不追求效率，只求与微博和平共处。所以在项目中加入了控制爬虫的频率的代码；

#### 1.3 目前本地代码与微博和平共处了5个月，所以涉及到的休眠时间用项目中设置的比较合适；

#### 1.4 项目从早上6点至晚上11点前每隔30分钟爬取一次。

#### 1.5 整个项目只有3个文件：
 - config.py 配置代码，比如项目根目录
 - auto_update.py 微博爬取代码，包括了微博内容、图片、视频
 - web.py 使用web框架bottle开发的微博展示页面（见后面截图）```

## 2.项目部署（ubuntu）

#### 2.0 安装必要包

- mongodb的安装参考：[官方文档](https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/)
- 使用pip安装：paste,bottle,pymongo,scrapy即可

#### 2.1 定时爬取微博

只需要在命令行执行```crontab -e```，然后加入下面一行代码即可：
```
*/30 * * * * /home/ruben/anaconda3/bin/python /home/ruben/git/weibo/auto_update.py
```
注意:上面的代码中需要替换成自己的python路径，以及自己的代码存放路径。


#### 2.2 开启web端
在命令行下根目录执行：
```
python web.py
```
即可。

这里可以自由设置需要展示的博主。如果需要添加或修改，只需要修改第六行代码即可。
比如只显示爱可可-爱生活：
```
id_names = {'1402400261': '爱可可-爱生活', }#uid:nick-name,查看博主主页即可获得uid。
```
## 3.PC端预览

<image src='pc.png' height=400/>

## 4.手机端预览

<image src='mobile.png' height=800 align="center"/>

最后如果觉得对您有帮助的吧，请我喝杯蜜雪冰城的原叶绿茶(4块)把～

<image src='zhifubao.jpg' height=400 align="middle"/>
