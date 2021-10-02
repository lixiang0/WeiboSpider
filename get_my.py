# coding=utf-8
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *

import requests
import logging
import random
import datetime
import time
import sys
import os
 
from youran.disks import Min
import pika,json
# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host='122.51.50.206'))
# channel = connection.channel()
# channel.queue_declare(queue='mblogs')
# import os

# os.system('cookie.exe  -b chrome -f json --dir results')
main = logging.getLogger('main')
main.setLevel(logging.DEBUG)
min = Min()
while True:
    
    # users = youran.db.count.random()
    ids=[]
    users =[user for user in  youran.db.count.random()]
    for user in users:
        # print(user)
        ids+=youran.db.follow.follows(user['_id'])#set(config.IDS)6390144374
    #youran.db.follow.follows(6390144374)#set(config.IDS)6390144374
    # ids=['1402400261']
    # print(ids)
    main.warning(ids)
    i = 0
    for uid in ids:
        uid=int(uid)
        username=youran.db.user.find_user(uid)['screen_name']
        
        main.warning(f'当前爬取的用户ID为：uid={uid}')
        # main.warning(f'当前爬取的用户ID为：uid={uid}')
        main.warning('*'*100)
        
        
        total_mblogs ,msg = youran.net.mblog.extract_mblogs(uid, 0,cookie=True,proxy=False)
        if total_mblogs<0:
            main.warning('当前请求失败，错误原因：'+repr(msg))
            main.warning('停止抓取,休息一会儿再爬取。。。。。。')
            utils.sleep(20*30, 30*60)
            continue
        total_page = int(total_mblogs/10)+1 if total_mblogs % 10 > 0 else int(total_mblogs/10)
        main.warning(f'当前计算得到总页数:{total_page},总博文数目:{total_mblogs}')

        current_page =2#total_page+2#- youran.db.mblog.pages(uid)
        while True:
            if current_page<1:
                break
            current_page -= 1  #因为db_mblogs.pages(uid)得到的页码是取整的，所以这里的开始页面为+1
            _page=total_page+2-current_page
            obj={'_id':str(uid)+str(_page),'uid':uid,'page':_page}
            # if youran.db.log.find(obj):
            #     main.warning(f'当前用户{username}第{current_page}已经爬取过，跳过.........')
            #     continue
            main.warning(f'当前用户为{username},爬取页数为：current_page={current_page}')
            main.warning('开始抽取本页中的博文：')
            TAG, mblogs = youran.net.mblog.extract_mblogs(uid, current_page,cookie=True,proxy=False)
            if not mblogs or TAG<0:  # 抓取太频繁   
                main.warning(f'抓取到了末尾，停止抓取。。。。。。TAG={TAG},info={mblogs}')
                utils.sleep(15, 60)
                break
            main.warning(f'抽取到用户：{username}总有{total_mblogs}条微博.......')
            
            main.warning(f'计算用户：{username}总有{total_page}页微博.......')
            main.warning('开始解析本页博文.........')
            main.warning('*'*100)
            for mblog in mblogs:

                timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],
                                             "%a %b %d %H:%M:%S %z %Y").timetuple())
                mblog['created_at1']=timeint
                utils.download_mblog(mblog,uid,current_page,total_page,duplicate=False,cookie=True,proxy=False)
            youran.db.log.add({'_id':str(uid)+str(_page),'uid':uid,'page':_page})
            utils.sleep(5, 10)
        main.warning(f'本id:{username}抓取结束..')
    youran.db.states.add({'name':'my_feeds','update_time':time.asctime( time.localtime(time.time()) )})
    utils.sleep(20*30, 30*60)

