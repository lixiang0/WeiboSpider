import os
os.environ["DBIP"]="192.168.8.111"
os.environ["MINIOIP"]="192.168.8.111"
os.environ["DBPort"]="27017"
os.environ["MINIOPort"]="9000"
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
# import os,logging,time
while True:
    try:
    # if True:
        text_herfs=net.hot.get()
        items=[(hot[0],hot[1]) for hot in text_herfs]
        if db.hot.add({'items':items}):
            # logger.warning('更新当前热点成功：')
            youran.logger.warning(items)
        for text,herf in text_herfs:
            url,bids=net.hot.get_detail(herf)
            youran.logger.warning(f'热点链接：{url},bids:{bids}')
            if bids:
                db.hotid.add({'url':url,'bids':bids})
                for bid in bids:
                    if bid:
                        # utils.download_mblog(mblog,current_page,total_page,duplicate=duplicate,cookie=cookie,proxy=proxy)
                        CODE,tag=youran.utils.download_mblog(mblog={'bid':bid,'isLongText':True},cookie=True,proxy=False)
                        if CODE==99:#存在且设定策略为不重复，目的是节省时间
                            continue
                        else:
                            youran.utils.sleep(5, 10)
        youran.utils.sleep(10*60,30*60)
    except Exception as e:
        youran.logger.error('遇到异常，错误为：'+repr(e))
        utils.sleep(10*60,40*60)