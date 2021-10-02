# coding=utf-8

import youran
from youran import db,utils
from youran.db import *
import logging
import random


logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)
while True:
    try:
        ids = set()
        for id in youran.db.follow.random_follows():
            if 'blogger' in id:
                ids.add(id['blogger'])
        logger.warning(ids)
        for uid in ids:
            import utils1
            code,msg=utils1.getall(uid=uid,duplicate=False,cookie=False,proxy=True)
            logger.warning(f'code={code},msg={msg}')
            utils.sleep(20,1*60)
    except Exception as e:
        logger.error('遇到异常，错误为：'+repr(e))
        utils.sleep(10*60,40*60)