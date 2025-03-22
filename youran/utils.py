import random,sys,datetime,time
from bs4 import BeautifulSoup
import youran
from youran import db,net,utils,logger

from youran.disks import Min
import math
from . import headers
min = Min()

def update_avatar(user):
    """更新用户头像并保存到MinIO存储"""
    if not user or '_id' not in user or 'avatar_hd' not in user:
        logger.warning(f"无效的用户数据，无法更新头像: {user}")
        return user
        
    uid = user['_id']
    img_url = user['avatar_hd']
    avatar_name = f'{uid}.jpg'
    
    try:
        logger.info(f"开始下载用户 {uid} 的头像: {img_url}")
        content = youran.net.img.download(img_url, progress=True, headers=headers.img, proxy=True)
        
        if not content:
            logger.warning(f"下载用户 {uid} 的头像失败")
            return user
            
        youran.utils.sleep(1, 5)
        min.save_weibo('avatar/' + avatar_name, content)
        logger.info(f"成功保存用户 {uid} 的头像")
        return user
    except Exception as e:
        logger.error(f"更新头像过程中发生错误: {repr(e)}")
        return user

def download_media(mblog):
    """下载微博中的图片和视频并保存到MinIO存储"""
    if not mblog:
        logger.warning("输入为空，无法下载媒体")
        return False
        
    try:
        # 下载图片
        success = _download_images(mblog)
        
        # 下载视频
        video_success = _download_video(mblog)
        
        return success or video_success
    except Exception as e:
        logger.error(f"下载媒体过程中发生错误: {repr(e)}")
        return False

def _download_images(mblog):
    """下载微博中的图片"""
    try:
        url_names = youran.net.img.extract(mblog)
        logger.warning(f'解析原微博中的图片')
        
        if not url_names:
            logger.warning(f'原微博中无图片')
            return False
            
        success = False
        for (url, name) in url_names:
            logger.warning(f'图片名称为:{name}')
            
            # 检查图片是否已存在
            if min.exist(name):
                logger.warning('该图片存在，跳过')
                success = True
                continue
                
            # 下载图片
            logger.warning(f'开始下载图片，URL:{url}')
            content = youran.net.img.download(url, progress=True, headers=headers.img)
            
            if content is None:
                logger.error('图片链接过时，跳过')
                continue
                
            # 保存图片
            logger.warning(f'下载成功，保存图片到minio中....name:{name}')
            min.save_weibo('imgs/' + name, content)
            logger.warning(f'保存图片成功')
            success = True
            
        return success
    except Exception as e:
        logger.error(f"下载图片过程中发生错误: {repr(e)}")
        return False

def _download_video(mblog):
    """下载微博中的视频"""
    try:
        video_url, video_name = youran.net.video.extract(mblog)
        logger.warning(f'解析原微博中的视频')
        
        if video_name is None:
            logger.warning(f'原微博中无视频')
            return False
            
        logger.warning(f'视频名称为:{video_name}')
        
        # 检查视频是否已存在
        if min.exist(video_name, t='videos'):
            logger.warning('该视频存在，跳过')
            return True
            
        # 下载视频
        logger.warning(f'开始下载视频，URL:{video_url}')
        _headers = headers.video
        
        if 'oasis.video.weibocdn.com' in video_url:
            _headers = headers.mobile
            
        content = youran.net.video.download(video_url, progress=True, headers=_headers)
        
        if content is None:
            logger.error('视频链接过时，跳过')
            return False
            
        # 保存视频
        logger.warning(f'下载成功，保存视频到minio中....name:{video_name}')
        min.save_weibo('videos/' + video_name, content)
        logger.warning(f'保存视频成功')
        return True
    except Exception as e:
        logger.error(f"下载视频过程中发生错误: {repr(e)}")
        return False

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
        time_line = ''
        if(t<60):
            time_line=f'{t} seconds'
            sleep_time-=1
        else:
            time_line=f'{int(t/60)} minutes'
            time.sleep(60)
        sys.stdout.write(f'\r{str(datetime.datetime.now())},sleep {time_line}..................')
        sleep_sec = 1 if t<60 else 60
        time.sleep(sleep_sec)
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

def getall(uid, duplicate=False, cookie=False, proxy=True, one_page=False, max_pages=5, max_retries=3):
    """
    获取用户的所有微博，并爬取相关数据
    
    Args:
        uid: 用户ID
        duplicate: 是否重复爬取已存在的微博
        cookie: 是否使用cookie
        proxy: 是否使用代理
        one_page: 是否只爬取第一页
        max_pages: 最多爬取页数
        max_retries: 单页失败后最大重试次数
        
    Returns:
        (状态码, 信息)
    """
    try:
        uid = int(uid)
        logger.warning(f'开始爬取用户ID: uid={uid}')
        
        # 获取用户信息
        user_info = _get_user_info(uid, cookie, proxy)
        if not user_info:
            return -1, "获取用户信息失败"
            
        username = user_info['screen_name']
        logger.warning(f'成功获取用户信息: uid={uid}, screen_name={username}')
        logger.warning('*'*100)
        
        # 获取总微博数和总页数
        total_mblogs, total_page = _get_user_blog_count(uid, cookie, proxy)
        if total_mblogs < 0:
            return -1, "获取微博总数失败"
            
        # 限制最大页数
        if max_pages > 0 and total_page > max_pages:
            logger.warning(f'限制爬取页数: {max_pages}/{total_page}')
            total_page = max_pages
            
        # 开始逐页爬取
        current_page = 1
        while current_page <= total_page:
            logger.warning(f'({uid}:{current_page}/{total_page})------当前用户为{username},爬取页数为：current_page={current_page}')
            
            # 尝试获取当前页的微博
            success, mblogs = _get_page_blogs(uid, current_page, max_retries, cookie, proxy)
            if not success:
                logger.warning(f'({uid}:{current_page}/{total_page})------爬取本页失败，跳过')
                current_page += 1
                continue
                
            # 处理每条微博
            for mblog in mblogs:
                _process_single_blog(uid, mblog, current_page, total_page, duplicate, cookie, proxy)
                
            # 随机休眠
            sleep(5, 10)
            
            # 是否只爬取一页
            if one_page:
                break
                
            current_page += 1
            
        logger.warning(f'本id:{uid}，用户名：{username}抓取结束..')
        logger.warning(f'总共{total_page}页微博,实际抓取到{current_page-1}页微博')      
        return 0, 'success'
        
    except Exception as e:
        logger.error(f"爬取用户 {uid} 过程中发生错误: {repr(e)}")
        return -1, f"发生错误: {str(e)}"
        
def _get_user_info(uid, cookie, proxy):
    """获取用户信息"""
    user_info = youran.db.user.find_users([uid])
    if len(user_info) > 0:
        return user_info[0]
        
    logger.warning(f'uid:{uid}不存在，从网络中抓取....')
    user_info = net.user.get(uid, cookie=cookie, proxy=proxy)
    if not user_info:
        logger.error(f'uid:{uid}抓取失败')
        return None
        
    logger.warning(f'uid:{uid}抓取成功....')
    return user_info
    
def _get_user_blog_count(uid, cookie, proxy):
    """获取用户微博数量和页数"""
    for retry in range(3):  # 最多重试3次
        total_mblogs, msg = youran.net.mblog.extract_mblogs(uid, 0, cookie=cookie, proxy=proxy)
        if total_mblogs and total_mblogs > 0:
            total_page = math.ceil(total_mblogs/10)
            logger.warning(f'当前计算得到总页数:{int(total_page)},总博文数目:{int(total_mblogs)}')
            return total_mblogs, total_page
        logger.warning(f'获取用户微博数量失败 (尝试 {retry+1}/3): {msg}')
        sleep(5, 10)  # 失败后休眠
        
    logger.warning('获取用户微博数量失败，停止抓取')
    return -1, 0
    
def _get_page_blogs(uid, page, max_retries, cookie, proxy):
    """获取指定页的微博列表"""
    for retry in range(max_retries):
        logger.warning(f'({uid}:{page})------开始抽取本页中的博文：(尝试 {retry+1}/{max_retries})')
        TAG, mblogs = youran.net.mblog.extract_mblogs(uid, page, cookie=cookie, proxy=proxy)
        
        if mblogs and TAG >= 0:
            logger.warning(f'({uid}:{page})------解析成功')
            return True, mblogs
            
        logger.warning(f'({uid}:{page})------抓取本页博文失败，TAG={TAG},info={mblogs}')
        sleep(10, 20)  # 失败后休眠更长时间
        
    return False, None
    
def _process_single_blog(uid, mblog, current_page, total_page, duplicate, cookie, proxy):
    """处理单条微博"""
    try:
        # 将创建时间转换为时间戳
        timeint = time.mktime(datetime.datetime.strptime(mblog['created_at'], 
                                             "%a %b %d %H:%M:%S %z %Y").timetuple())
        mblog['created_at1'] = timeint
        
        # 下载微博内容
        CODE, tag = utils.download_mblog(mblog, current_page, total_page, 
                                     duplicate=duplicate, cookie=cookie, proxy=proxy)
                                     
        # 如果微博已存在且不需要重复抓取，只更新评论
        if CODE == 99:
            logger.warning(f'({uid}:{current_page}/{total_page})-------开始解析评论..')
            comments = download_comment(mblog, maxid=None, cookie=cookie, proxy=proxy)
            if comments:
                logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中..')
                youran.db.comment.add(comments)
                logger.warning(f'({uid}:{current_page}/{total_page})-------添加到数据库中成功..')
            else:
                logger.error(f'({uid}:{current_page}/{total_page})-------解析评论失败..')
            return
            
        sleep(5, 10)
        
        # 处理转发微博
        if 'retweeted_status' in mblog:
            rblog = mblog['retweeted_status']
            rblog = {'bid': rblog['bid'], 'isLongText': True}
            utils.download_mblog(rblog, current_page, total_page, 
                             duplicate=duplicate, cookie=cookie, proxy=proxy)
            sleep(5, 10)
    except Exception as e:
        logger.error(f"处理微博过程中发生错误: {repr(e)}")
        # 继续处理下一条微博

if __name__ == '__main__':
    print()
    # -------开始解析bid为EEu765A7V的博文
    download_mblog({'bid':'EEu765A7V','mid':5630886590475490824,'isLongText':True,'text':'111','created_at':'Tue Jul 19 10:35:49 +0800 2011'},1,1,1,duplicate=True)
