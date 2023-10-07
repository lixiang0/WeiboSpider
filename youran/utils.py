import random,sys,datetime,time
from bs4 import BeautifulSoup
import youran
from youran import db,net,utils,logger

from youran.disks import Min
import math
from . import headers
min = Min()

def update_avatar(user):
    #更新头像
    #avatar/uid.jpg
    uid=user['_id']
    img_url=user['avatar_hd']
    avatar_name=f'{uid}.jpg'
    content=youran.net.img.download(img_url,progress=True,headers=headers.img,proxy=True)
    youran.utils.sleep(1,5)
    min.save_weibo('avatar/'+avatar_name,content )
    return user
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
        content=youran.net.img.download(url,progress=True,headers=headers.img)
        if content is None:
            logger.error('图片链接过时，跳过')
            return False
        logger.warning(f'下载成功，保存图片到minio中....name:{name}')
        min.save_weibo('imgs/'+name,content )
        logger.warning(f'保存图片成功...')
    else:
        logger.warning(f'原微博中无图片........')
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
        _headers=headers.video
        if 'oasis.video.weibocdn.com' in video_url:
            _headers=headers.mobile
        content=youran.net.video.download(video_url,progress=True,headers=_headers)
        if content is None:
            logger.error('视频链接过时，跳过')
            return False
        logger.warning(f'下载成功，保存视频到minio中....name:{video_name}')
        min.save_weibo('videos/'+video_name, content)
        logger.warning(f'保存视频成功...')
    else:
        logger.warning(f'原微博中无视频........')

    return True

def download_comment(mblog,maxid=None,cookie=False,proxy=False):
    comments =None
    try:
        comments= youran.net.comment.get(mblog,maxid,cookie,proxy)
    except Exception as e:
        logger.error(f'更新评论错误：')
        logger.error(repr(e))
    if comments is None:
        return None
    else:
        if 'data' in comments :
            if 'data' in comments['data']:
                logger.warning(f'解析到微博中评论：{cleanhtml(comments["data"]["data"][0]["text"])}')
        return comments 
'''
-1 错误
'''
def download_mblog(mblog,current_page=-1,total_page=-1,duplicate=False,cookie=False,proxy=False):
    uid='-1'
    logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析bid为{mblog["bid"]}的博文')
    if mblog is None:
        logger.error(f'({uid}:{current_page}/{total_page})-------mblog为空...')
        logger.error(f'({uid}:{current_page}/{total_page})-------停止解析本博文')
        logger.warning('*'*100)
        return -1,'解析出错'
    ttime=time.time()
    #如果存在，是否重复
    if youran.db.mblog.exists({'bid':mblog['bid']}):
        logger.warning(f'({uid}:{current_page}/{total_page})-------bid为{mblog["bid"]}的博文已存在')
        if not duplicate:
            logger.warning(f'({uid}:{current_page}/{total_page})-------更新策略为不重复，跳过')
            return 99,'exists and not duplicate'
    #有些mblog中没有user
    user=None
    if 'user' in mblog:
        if 'id' in mblog['user']:
            uid=mblog['user']['id']
            logger.warning(f'({uid}:{current_page}/{total_page})-------解析博文{mblog["bid"]}的作者:{uid}')
    #mblog中不存在用户的id，那就更新mblog
    if user is None:
        logger.warning(f'({uid}:{current_page}/{total_page})-------uid为空，非标准的mblog，重新网络抓取mblog。')
        mblog = youran.net.mblog.get(mblog,cookie=cookie,proxy=proxy)
        if mblog is None:
            logger.error(f'({uid}:{current_page}/{total_page})-------更新博文失败')
            return -1,'更新博文失败'
        uid=mblog['user']['id']
        logger.warning(f'({uid}:{current_page}/{total_page})-------抓取{mblog["bid"]}的作者:{uid}')
    mblog['uid']=uid #在mblog中添加uid
    mblog['spider_time']=time.time() #当前爬取的时间
    timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],"%a %b %d %H:%M:%S %z %Y").timetuple())
    mblog['created_at1']=timeint #博文发布的时间
    if 'mblogid' in mblog: #兼容mblogid和bid
        mblog['bid']=mblog['mblogid']
    logger.warning(f'({uid}:{current_page}/{total_page})-------解析到内容为：{utils.cleanhtml(mblog["text"])}')
    logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中..')
    youran.db.mblog.add(mblog)
    logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中成功..')
    logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析评论..')
    comments=download_comment(mblog,maxid=None,cookie=cookie,proxy=proxy)
    if comments:
        logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中..')
        youran.db.comment.add(comments)
        logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中成功..')
    else:
        logger.error(f'({uid}:{current_page}/{total_page})-------解析评论失败..')
    logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析视频：')
    try:
        download_media(mblog)
    except Exception as e:
        logger.error(f'({uid}:{current_page}/{total_page})-------解析视频失败：{repr(e)}')
    _speed=1/(time.time()-ttime)
    logger.warning(f'({uid}:{current_page}/{total_page})-------抓取速度为：'+str(_speed)+'条/秒')
    return 0,'success'
def sleep(s=10,e=30):
    sleep_time = random.randint(s, e)
    for t in [_ for _ in range(0, sleep_time)][::-1]:
        sys.stdout.write(f'\r{str(datetime.datetime.now())},sleep {t} seconds....')
        time.sleep(1)
        sleep_time-=1
    # print('\n')
def isnewday():
    from datetime import datetime, time
    now = datetime.now()
    year=now.year
    hour="{:02d}".format(now.hour)
    day="{:02d}".format(now.day)
    month="{:02d}".format(now.month)
    if now.hour==0 and now.minute==0:
        return True,year,month,day,hour
    return False,year,month,day,hour

import re
def cleanhtml(raw_html):
    cleantext = BeautifulSoup(raw_html, "lxml").text
    return cleantext

def getall(uid,duplicate=False,cookie=False,proxy=True,one_page=False):
    uid=int(uid)
    user_info=youran.db.user.find_users([uid])
    if not len(user_info)>0:
        logger.warning(f'uid:{uid}不存在，从网络中抓取....')
        user_info=[net.user.get(uid)]
        logger.warning(f'uid:{uid}抓取成功....')
    username=user_info[0]['screen_name']
    logger.warning(f'当前爬取的用户ID为：uid={uid},screen_name={username}')
    logger.warning('*'*100)
    total_mblogs ,msg = youran.net.mblog.extract_mblogs(uid, 0,cookie=cookie,proxy=proxy)
    if not total_mblogs or total_mblogs<0:
        logger.warning('当前请求失败，错误原因：'+str(msg))
        logger.warning('停止抓取,休息一会儿再爬取。。。。。。')
        return -1,msg

    total_page = math.ceil(total_mblogs/10)
    logger.warning(f'当前计算得到总页数:{int(total_page)},总博文数目:{int(total_mblogs)}')
    current_page =1
    count_spider_page=current_page
    while True:
        if current_page>total_page:# 原因：total_page+1--> 1+1
            break
        logger.warning(f'({uid}:{current_page}/{total_page})------当前用户为{username},爬取页数为：current_page={current_page}')
        logger.warning(f'({uid}:{current_page}/{total_page})------开始抽取本页中的博文：')
        TAG, mblogs = youran.net.mblog.extract_mblogs(uid, current_page,cookie=cookie,proxy=proxy)
        if not mblogs or TAG<0:  # 抓取太频繁   
            logger.warning(f'({uid}:{current_page}/{total_page})------抓取本页博文失败，TAG={TAG},info={mblogs}')
            return -1,mblogs
        logger.warning(f'({uid}:{current_page}/{total_page})------解析成功.........')
        logger.warning(f'({uid}:{current_page}/{total_page})------开始解析本页博文.........')
        logger.warning('*'*100)
        for mblog in mblogs:
            #Tue Sep 28 20:12:48 2021
            timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],
                                                    "%a %b %d %H:%M:%S %z %Y").timetuple())
            mblog['created_at1']=timeint
            CODE,tag=utils.download_mblog(mblog,current_page,total_page,duplicate=duplicate,cookie=cookie,proxy=proxy)
            if CODE==99:#存在且设定策略为不重复则只抓取评论，目的是节省时间
                logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析评论..')
                comments=download_comment(mblog,maxid=None,cookie=cookie,proxy=proxy)
                if comments:
                    logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中..')
                    youran.db.comment.add(comments)
                    logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中成功..')
                else:
                    logger.error(f'({uid}:{current_page}/{total_page})-------解析评论失败..')
                continue
            else:
                utils.sleep(5, 10)
            if 'retweeted_status' in mblog:
                rblog=mblog['retweeted_status']
                rblog={'bid':rblog['bid'],'isLongText':True}
                utils.download_mblog(rblog,current_page,total_page,duplicate=duplicate,cookie=cookie,proxy=proxy)
                utils.sleep(5, 10)
        utils.sleep(5, 10)
        
        if one_page:
            break
        #只爬取前五页，不需要全爬
        if current_page>5:
            break
        current_page += 1
    logger.warning(f'本id:{uid}，用户名：{username}抓取结束..')
    logger.warning(f'总共{total_page}页微博,实际抓取到{current_page}页微博')      
    return 0,'success'


if __name__ == '__main__':
    print()
    # -------开始解析bid为EEu765A7V的博文
    download_mblog({'bid':'EEu765A7V','mid':5630886590475490824,'isLongText':True,'text':'111','created_at':'Tue Jul 19 10:35:49 +0800 2011'},1,1,1,duplicate=True)
