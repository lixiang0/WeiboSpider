import os
# export   DBIP=192.168.8.101
# export   MINIOIP=192.168.8.101
# export   DBPort=27017 
# export  MINIOPort=9000
os.environ["DBIP"]="192.168.8.111"
os.environ["MINIOIP"]="192.168.8.111"
os.environ["DBPort"]="27017"
os.environ["MINIOPort"]="9000"
import youran

from youran import db,net,utils

import requests
import logging
import random
import datetime
import time
import sys

 
from youran.disks import Min
import json
# os.system('cookie.exe  -b chrome -f json --dir results')
main = logging.getLogger('main')
main.setLevel(logging.DEBUG)
min = Min()
while True:
    ids=[]
    users =[user for user in  youran.db.account.random()]
    for user in users:
        youran.logger.warning(user['_id'])
        ids+=db.follow.find_follows(id=user['_id'])#set(config.IDS)6390144374
    youran.logger.warning(ids)
    # ids=youran.db.follow.find_follows(id=6390144374)
    i = 0
    for uid in ids:
        uid=int(uid['blogger'])
        youran.logger.warning(f'当前爬取的用户ID为：{uid}')
        username=list(db.user.find({'_id':uid}))[0]['screen_name']
        youran.logger.warning(f'当前爬取的用户为：{username}')
        youran.logger.warning('*'*100)
        code,msg=utils.getall(uid=uid,duplicate=False,cookie=False,proxy=False,one_page=True)
        youran.logger.warning(f'code={code},msg={msg}')
        youran.utils.sleep(20,1*60) 
        youran.logger.warning(f'本id:{username}抓取结束..')
    utils.sleep(10*30, 30*60)

