import random,sys,datetime,time
from bs4 import BeautifulSoup
import youran
from youran import db,net,utils,logger

from youran.disks import Min
import math

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
    if uid =='uid':
        mblog = youran.net.mblog.get(mblog,cookie=cookie,proxy=proxy)
        if mblog is None:
            return -1,'解析出错'
        uid=mblog['user']['id']
    current_page=-1 if current_page=='current_page' else current_page
    total_page=-1 if total_page=='total_page' else total_page
    if db.mblog.exists({'bid':mblog['bid']}) and not duplicate:
        logger.warning(f'({uid}:{current_page}/{total_page})-------bid为{mblog["bid"]}的博文已存在，跳过')
        logger.warning(f'({uid}:{current_page}/{total_page})-------开始更新评论..')
        comments =None
        try:
            comments= youran.net.comment.get(mblog,cookie=cookie,proxy=proxy)
        except Exception as e:
            logger.warning(repr(e))
        if comments is not None:
            if 'data' in comments :
                if 'data' in comments['data']:
                    logger.warning(f'({uid}:{current_page}/{total_page})-------更新到原微博中评论：{comments["data"]["data"][0]["text"]}')
            db.comment.add(comments)
        return -1,'bid已存在'
    logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析bid为{mblog["bid"]}的博文')
    mblog = youran.net.mblog.get(mblog,cookie=cookie,proxy=proxy)  #mblog or None
    if mblog is None:
        logger.error(f'({uid}:{current_page}/{total_page})-------解析{mblog}出错........')
        logger.error(f'({uid}:{current_page}/{total_page})-------停止解析本博文')
        logger.warning('*'*100)
        return -1,'解析出错'
    else:#not   None
        mblog['uid']=uid
        mblog['spider_time']=time.time() #当前爬取的时间
        timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],
                                                        "%a %b %d %H:%M:%S %z %Y").timetuple())
        mblog['created_at1']=timeint
        if 'mblogid' in mblog:
            mblog['bid']=mblog['mblogid']
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

import re
def cleanhtml(raw_html):
    cleantext = BeautifulSoup(raw_html, "lxml").text
    return cleantext

def getall(uid,duplicate=False,cookie=False,proxy=True,one_page=False):
    uid=int(uid)
    user_count=youran.db.user.find_users([uid])
    if not len(user_count)>0:
        logger.warning(f'uid:{uid} not exists')
        user_count=[net.user.get(uid)]
    username=user_count[0]['screen_name']
    logger.warning(f'当前爬取的用户ID为：uid={uid},username={username}')
    logger.warning('*'*100)
    total_mblogs ,msg = youran.net.mblog.extract_mblogs(uid, 0,cookie=cookie,proxy=proxy)
    if total_mblogs is None or total_mblogs<0:
        logger.warning('当前请求失败，错误原因：'+str(msg))
        logger.warning('停止抓取,休息一会儿再爬取。。。。。。')
        return -1,msg

    total_page = math.ceil(total_mblogs/10)
    logger.warning(f'当前计算得到总页数:{int(total_page)},总博文数目:{int(total_mblogs)}')
    current_page =1#100 if total_page>100 else total_page+1  #这里加1是因为while循环总是先减一
    count_spider_page=current_page
    while True:
        if current_page>total_page:# 原因：total_page+1--> 1+1
            break
        _page=total_page-current_page  #存储到数据库中，最后一页编号为1。这里与微博相反。
        obj={'_id':str(uid)+str(_page),'uid':uid,'page':_page}
        if youran.db.log.find(obj) and not duplicate:#存在 且不重复
            logger.warning(f'({uid}:{current_page}/{total_page})------当前用户{username}第{current_page}已经爬取过且duplicate={duplicate}，跳过.........')
            continue
        logger.warning(f'({uid}:{current_page}/{total_page})------当前用户为{username},爬取页数为：current_page={current_page}')
        logger.warning(f'({uid}:{current_page}/{total_page})------开始抽取本页中的博文：')
        TAG, mblogs = youran.net.mblog.extract_mblogs(uid, current_page,cookie=cookie,proxy=proxy)
        if not mblogs or TAG<0:  # 抓取太频繁   
            logger.warning(f'({uid}:{current_page}/{total_page})------抓取到了末尾，停止抓取。。。。。。TAG={TAG},info={mblogs}')
            return -1,mblogs
        logger.warning(f'({uid}:{current_page}/{total_page})------解析成功.........')
        logger.warning(f'({uid}:{current_page}/{total_page})------开始解析本页博文.........')
        logger.warning('*'*100)
        for mblog in mblogs:
            #Tue Sep 28 20:12:48 2021
            timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],
                                                    "%a %b %d %H:%M:%S %z %Y").timetuple())
            mblog['created_at1']=timeint
            #   duplicate=False for download blog
            utils.download_mblog(mblog,uid,current_page,total_page,duplicate=False,cookie=cookie,proxy=proxy)
            utils.sleep(5, 10)
            if 'retweeted_status' in mblog:
                rblog=mblog['retweeted_status']
                rblog={'bid':rblog['bid'],'isLongText':True}
                utils.download_mblog(rblog,'uid',current_page,total_page,duplicate=False,cookie=cookie,proxy=proxy)
                utils.sleep(5, 10)
        youran.db.log.add({'_id':str(uid)+str(_page),'uid':uid,'page':_page})
        utils.sleep(5, 10)
        current_page += 1
        if one_page:
            break
    logger.warning(f'本id:{uid}，用户名：{username}抓取结束..')
    logger.warning(f'总共{total_page}页微博,实际抓取到{count_spider_page-current_page+1}页微博')      
    youran.db.states.add({'name':'更新所有微博：','update_time':time.asctime( time.localtime(time.time()) )})
    return 0,'success'


if __name__ == '__main__':
    print()
    # -------开始解析bid为EEu765A7V的博文
    download_mblog({'bid':'EEu765A7V','mid':5630886590475490824,'isLongText':True,'text':'111','created_at':'Tue Jul 19 10:35:49 +0800 2011'},1,1,1,duplicate=True)
