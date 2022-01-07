# coding=utf-8
import os
os.environ['DBIP']='192.168.1.14'
os.environ['MINIOIP']='192.168.1.9'
os.environ['DBPort']='27017'
os.environ['MINIOPort']='9010'

import youran

from youran import db,net,utils

import requests
import logging
import random
import datetime
import time
import sys
import os
 
from youran.disks import Min
import json
# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host='122.51.50.206'))
# channel = connection.channel()
# channel.queue_declare(queue='mblogs')
# import os

# os.system('cookie.exe  -b chrome -f json --dir results')
logging.basicConfig(filename='my.log',
                            filemode='w',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
main = logging.getLogger('main')
main.setLevel(logging.DEBUG)
min = Min()
# youran.db.db_client = pymongo.MongoClient(f"mongodb://{os.environ['DBIP']}:{os.environ['DBPort']}/")["db_weibo2"]
while True:
    
    # users = youran.db.count.random()
    ids=[]
    users =[user for user in  db.account.random()]
    for user in users:
        print(user)
        ids+=db.follow.find_follows(id=user['_id'])#set(config.IDS)6390144374
    #youran.db.follow.follows(6390144374)#set(config.IDS)6390144374
    #ids=['1402400261']
    # ids=[2014433131]
    # print(ids)
    main.warning(ids)
    i = 0
    for uid in ids:
        uid=int(uid['blogger'])
        main.warning(f'当前爬取的用户ID为：{uid}')
        username=list(db.user.find({'_id':uid}))[0]['screen_name']
        main.warning(f'当前爬取的用户为：{username}')
        main.warning('*'*100)
        
        current_page =0#639#total_page- youran.db.mblog.pages(uid)
        sameid=0
        while True:
            if current_page>0 :#or sameid>15:
            #     sameid=0
                break
            current_page += 1  #因为db_mblogs.pages(uid)得到的页码是取整的，所以这里的开始页面为+1
            _page=current_page
            obj={'_id':str(uid)+str(_page),'uid':uid,'page':_page}
            main.warning(f'当前用户为{username},爬取页数为：current_page={current_page}')
            main.warning(f'开始抽取{current_page}页中的博文：')
            TAG, mblogs = net.mblog.extract_mblogs1(uid, current_page,cookie=True,proxy=False)
            if TAG==-2 or TAG==-3:  # 抓取太频繁 或者网络错误
                main.warning(f'抓取太频繁或者网络错误，休息一会儿再继续抓取。。。。。。TAG={TAG},info={mblogs}')
                utils.sleep(5*60, 10*60)
                current_page-=1
                continue
            if TAG==-1 or len(mblogs)==0:
                main.warning(f'抓取到了末尾，停止抓取。。。。。。')
                break
            main.warning(f'开始解析本页博文,共：{len(mblogs)}条.........')
            main.warning('*'*100)
            for mblog in mblogs:
                # if sameid>15:
                #     break
                # mblog['uid']=uid
                # mblog['duplicate']=True
                # send.send(mblog)
                # timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],
                #                              "%a %b %d %H:%M:%S %z %Y").timetuple())
                # mblog['created_at1']=timeint
                mblog['bid']=mblog['mblogid']
                code,msg=utils.download_mblog(mblog,uid,current_page,9999,duplicate=False,cookie=True,proxy=False)
                if code==-1:
                    sameid+=1
                if 'retweeted_status' in mblog:
                    mblog['retweeted_status']['bid']=mblog['retweeted_status']['mblogid']
                    code,msg=utils.download_mblog(mblog['retweeted_status'],uid,current_page,9999,duplicate=False,cookie=True,proxy=False)
                # mblog['isLongText']=True
                # mblog['duplicate']=False
                # b=json.dumps(mblog).encode()
                # channel.basic_publish(exchange='', routing_key='mblogs', body=b)
                utils.sleep(1, 3)
            utils.sleep(1, 5)
            db.log.add({'_id':str(uid)+str(_page),'uid':uid,'page':_page})
            
        main.warning(f'本id:{username}抓取结束..')
        # main.warning(f'总共{total_mblogs1}条微博,实际抓取到{youran.db.mblog.count(uid)},总共{total_page}页微博,实际抓取到{current_page}页微博')      
        # main.removeHandler(handler)
    db.States().add({'name':'我的关注','update_time':time.asctime( time.localtime(time.time()) )})
    utils.sleep(20*30, 30*60)

