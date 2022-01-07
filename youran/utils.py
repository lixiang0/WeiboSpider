import requests
import json
import logging

import os
import random,sys,datetime,time
from bs4 import BeautifulSoup
import youran
from youran import db,net,utils

from youran.disks import Min

logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)
# log = logging.StreamHandler()
# logger.setFormatter(logging.Formatter('%(levelname)s - %(asctime)s - %(message)s'))
# logger.addHandler(log)
min = Min()
def download_media(mblog):
        # main.warning(mblog.keys())
    url_names = youran.net.img.extract(mblog)
    logger.warning(f'解析原微博中的图片：')
    for (url, name) in url_names:
        logger.warning(f'图片名称为:{name}')
        if min.exist(name):
            logger.warning('该图片存在，跳过。。。')
            return True
        logger.warning(f'开始下载图片，URL:{url}')
        content=youran.net.img.download(url,progress=True)
        if content is None:
            logger.warning('图片链接过时，跳过')
            return False
        min.save_weibo('imgs/'+name,content )
    video_url, video_name = youran.net.video.extract(mblog)
    logger.warning(f'解析原微博中的视频：')
    if video_name is not None:
        # video_name=mblog['bid']+video_name
        # name=video_name
        logger.warning(f'视频名称为:{video_name}')
        if min.exist(video_name,t='videos'):
            logger.warning('该视频存在，跳过。。。')
            return True
        logger.warning(f'开始下载视频，URL:{video_url}')
        content=youran.net.video.download(video_url,progress=True)
        if content is None:
            logger.warning('视频链接过时，跳过')
            return False
        min.save_weibo('videos/'+video_name, content)
    return True

def download_mblog(mblog,uid,current_page,total_page,duplicate=False,cookie=False,proxy=False):
    ttime=time.time()
    # uid=mblog['user']['id'] 
    # mblog['bid']=mblog['mblogid']
    if db.mblog.exists({'bid':mblog['bid']}) and not duplicate:
        logger.warning(f'({uid}:{current_page}/{total_page})-------bid为{mblog["bid"]}的博文已存在，跳过')
        return -1,'bid已存在'
    logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析bid为{mblog["bid"]}的博文')
    mblog = youran.net.mblog.get(mblog,cookie=cookie,proxy=proxy)  #mblog or None
    if mblog is None:
        logger.error(f'({uid}:{current_page}/{total_page})-------解析{mblog}出错........')
        logger.error(f'({uid}:{current_page}/{total_page})-------停止解析本博文')
        logger.warning('*'*100)
        return -1,'解析出错'
    mblog['uid']=uid
    mblog['spider_time']=time.time() #当前爬取的时间
    timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],
                                                    "%a %b %d %H:%M:%S %z %Y").timetuple())
    mblog['created_at1']=timeint
    if 'mblogid' in mblog:
        mblog['bid']=mblog['mblogid']
    if mblog is not None:
        logger.warning(f'({uid}:{current_page}/{total_page})-------解析到内容为：{utils.cleanhtml(mblog["text"])}')
        logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中..')
        if db.mblog.add(mblog):
            logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中成功..')
        else:
            logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中失败，错误原因：重复bid..')
        logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析评论..')
        comments =None
        try:
            comments= youran.net.comment.get(mblog,cookie=cookie,proxy=proxy)
        except Exception as e:
            logger.warning(repr(e))
        if comments is not None:
            if 'data' in comments :
                if 'data' in comments['data']:
                    logger.warning(f'({uid}:{current_page}/{total_page})-------解析到原微博中评论：{comments["data"]["data"][0]["text"]}')
            db.comment.add(comments)
        logger.warning(f'({uid}:{current_page}/{total_page})-------解析视频：')
        try:
            download_media(mblog)
        except Exception as e:

            logger.error(f'.....error video download............\n{repr(e)}')
    speeed=1/(time.time()-ttime)
    logger.warning(f'({uid}:{current_page}/{total_page})-------抓取速度为：'+str(speeed)+'条/秒')
    return 0,'success'
def sleep(s=10,e=30):
    sleep_time = random.randint(s, e)
    for t in [_ for _ in range(0, sleep_time)][::-1]:
        sys.stdout.write(f'\r{str(datetime.datetime.now())},sleep {t} seconds....')
        time.sleep(1)
        sleep_time-=1
    # print('\n')
def download_hot():
    hots=youran.net.hot.get()
    items=[(hot[0],hot[1]) for hot in hots]
    if db.hot.add({'items':items}):
        logger.warning('更新当前热点成功：')
        logger.warning(items)
    for hot in hots:
        bids=hot[2]
        url=hot[1]
        # print(url,bids)
        logger.warning(f'热点链接：{url},bids:{bids}')
        if bids:
            db.hotid.add({'url':url,'bids':bids})
            for bid in bids:
                if bid:
                    download_mblog({'bid':bid,'isLongText':True},'uid','current_page','total_page',duplicate=True,proxy=True)
import re
def cleanhtml(raw_html):
    cleantext = BeautifulSoup(raw_html, "lxml").text
    return cleantext




if __name__ == '__main__':
    print()
    # -------开始解析bid为EEu765A7V的博文
    download_mblog({'bid':'EEu765A7V','mid':5630886590475490824,'isLongText':True,'text':'111','created_at':'Tue Jul 19 10:35:49 +0800 2011'},1,1,1,duplicate=True)
