
import youran
from youran import db,utils
from youran.db import *

while True:
    try:
        ids = set([1865990891])#2014433131
        # ids = set([2014433131])#
        if False:
            ids = set()
            # for id in db.account.find({}):
            #     ids.add(id['_id'])
            for id in db.follow.random():
                if 'blogger' in id:
                    ids.add(id['blogger'])
        # logger.warning(ids)
        # if len(ids)==0:
        #     break
        for uid in ids:
            #   duplicate=False for download bug ,if True ,download once only
            code,msg=utils.getall(uid=uid,duplicate=True,cookie=False,proxy=True)
            youran.logger.warning(f'code={code},msg={msg}')
            utils.sleep(20,1*60)
    except Exception as e:
        youran.logger.error('遇到异常，错误为：'+repr(e))
        utils.sleep(10*60,40*60)
