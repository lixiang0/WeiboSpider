# coding=utf-8
#环境变量的设置，必须在import youran之前引入
# import os
# os.environ['DBIP']='192.168.1.14'
# os.environ['MINIOIP']='192.168.1.9'
# os.environ['DBPort']='27017'
# os.environ['MINIOPort']='9010'

import youran
from youran import db,utils
from youran.db import *
import logging
import random
logging.basicConfig(filename='all.log',
                            filemode='w',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
logger = logging.getLogger('main')

logger.setLevel(logging.DEBUG)

while True:
    try:
        # ids = set([2014433131])
        ids = set()
        for id in db.follow.random():
            if 'blogger' in id:
                ids.add(id['blogger'])
        # logger.warning(ids)
        # if len(ids)==0:
        #     break
        for uid in ids:
            import utils1
            code,msg=utils1.getall(uid=uid,duplicate=True,cookie=False,proxy=True)
            logger.warning(f'code={code},msg={msg}')
            utils.sleep(20,1*60)
    except Exception as e:
        logger.error('遇到异常，错误为：'+repr(e))
        utils.sleep(10*60,40*60)
