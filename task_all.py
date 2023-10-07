
import youran
from youran import db,utils
from youran.db import *

while True:
    try:
        # ids = set([3164402322])#2014433131
        # ids = set([2014433131])#
        # if False:
        ids = set()
        # for id in db.account.find({}):
        #     ids.add(id['_id'])
        for id in db.follow.random(20000):
            if 'blogger' in id:
                ids.add(id['blogger'])
        # logger.warning(ids)
        # if len(ids)==0:
        #     break
        for uid in ids:
            #   duplicate=False：不重复，True就重复。
            code,msg=utils.getall(uid=uid,duplicate=False,cookie=False,proxy=True,one_page=False)
            youran.logger.warning(f'code={code},msg={msg}')
            # utils.sleep(20,1*60)
    except Exception as e:
        youran.logger.error('遇到异常，错误为：'+repr(e))
        utils.sleep(10*60,40*60)
