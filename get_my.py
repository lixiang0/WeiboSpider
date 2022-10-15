# coding=utf-8
import os
os.environ['DBIP']='192.168.1.9'
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
# os.system('cookie.exe  -b chrome -f json --dir results')
main = logging.getLogger('main')
main.setLevel(logging.DEBUG)
min = Min()
while True:
    ids=[]
    users =[user for user in  db.account.random()]
    for user in users:
        print(user)
        ids+=db.follow.find_follows(id=user['_id'])#set(config.IDS)6390144374
    main.warning(ids)
    i = 0
    for uid in ids:
        uid=int(uid['blogger'])
        main.warning(f'当前爬取的用户ID为：{uid}')
        username=list(db.user.find({'_id':uid}))[0]['screen_name']
        main.warning(f'当前爬取的用户为：{username}')
        main.warning('*'*100)
        code,msg=utils.getall(uid=uid,duplicate=True,cookie=True,proxy=False,one_page=True)
        youran.logger.warning(f'code={code},msg={msg}')
        utils.sleep(20,1*60) 
        main.warning(f'本id:{username}抓取结束..')
        # main.warning(f'总共{total_mblogs1}条微博,实际抓取到{youran.db.mblog.count(uid)},总共{total_page}页微博,实际抓取到{current_page}页微博')      
        # main.removeHandler(handler)
    db.States().add({'name':'我的关注','update_time':time.asctime( time.localtime(time.time()) )})
    utils.sleep(20*30, 30*60)

