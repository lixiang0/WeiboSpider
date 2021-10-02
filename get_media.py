import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
import logging
from youran.disks import Min
from tqdm import tqdm
main = logging.getLogger('main')
main.setLevel(logging.DEBUG)


while True:
    mblogs = list(youran.db.mblog.random(1000))
    with tqdm(total=len(mblogs),postfix=dict,mininterval=0.3) as pbar:
        for mblog in mblogs:
            try:

                redown=False
                try:
                    redown = not utils.download_media(mblog)
                except Exception as e:
                    redown=True
                
                if redown:
                    mblog['isLongText']=True
                    mblog['duplicate']=True
                    print('视频链接超时，重新获取')
                    utils.download_mblog(mblog,mblog['user']['id'],1,1,duplicate=True,cookie=False,proxy=True)
                else:
                    print(mblog['text'],'不需要更新')

            except Exception as e:
                main.error('error.....retry download............')
                main.error(repr(e))

            pbar.update(1)

    
