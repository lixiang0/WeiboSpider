import os
os.environ["DBIP"]="192.168.8.111"
os.environ["MINIOIP"]="192.168.8.111"
os.environ["DBPort"]="27017"
os.environ["MINIOPort"]="9000"
import sys
import time
import json
import re
import argparse
import logging
import random
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 添加项目根目录到sys.path，确保能正确导入youran模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youran
from youran import utils, net, db
from youran.disks import Min
min=Min()
# 配置日志
def setup_logger(log_file='weibo_spider.log', level=logging.INFO, max_size=10*1024*1024, backup_count=5):
    """
    设置日志记录器
    
    Args:
        log_file: 日志文件名
        level: 日志级别
        max_size: 单个日志文件最大大小（字节）
        backup_count: 保留的日志文件数量
        
    Returns:
        配置好的logger实例
    """
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_path = os.path.join(log_dir, log_file)
    
    # 创建logger
    logger = logging.getLogger('weibo_spider')
    logger.setLevel(level)
    
    # 清除已存在的处理器，避免重复
    if logger.handlers:
        logger.handlers = []
    
    # 创建文件处理器，使用RotatingFileHandler进行日志轮转
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=max_size, 
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 设置不同级别的日志处理
    file_handler.setLevel(level)
    console_handler.setLevel(level)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志记录器
logger = setup_logger()

# 创建media_urls集合（如果不存在）
def ensure_media_collection():
    """确保media_urls集合存在"""
    try:
        # 检查集合是否存在 - 在MongoDB中，集合在第一次插入数据时会自动创建
        # 此处我们可以直接通过尝试获取统计信息来判断集合是否正常工作
        try:
            stats = youran.db.media_urls.get_stats()
            logger.info(f"media_urls集合存在，当前状态: 总计: {stats['total']}，待下载: {stats['pending']}，已下载: {stats['success']}，失败: {stats['failed']}，跳过: {stats['skipped']}")
        except Exception:
            logger.info("media_urls集合不存在或无数据，将创建索引")
            # 为常用查询字段创建索引
            youran.db.media_urls.db.create_index([('download_status', 1)])
            youran.db.media_urls.db.create_index([('bid', 1)])
            youran.db.media_urls.db.create_index([('uid', 1)])
            youran.db.media_urls.db.create_index([('add_time', 1)])
            youran.db.media_urls.db.create_index([('media_type', 1)])
            logger.info("创建索引成功")
    except Exception as e:
        logger.error(f"创建或检查media_urls集合出错: {repr(e)}")

# 调用函数确保集合存在
ensure_media_collection()
def download_media(media, use_proxy=True, max_retries=1):
    """
    下载单个媒体文件
    
    Args:
        media: 媒体记录
        use_proxy: 是否使用代理
        max_retries: 最大重试次数
        
    Returns:
        (success, file_content) 元组
    """
    media_id = media['_id']
    media_url = media['media_url']
    media_type = media['media_type']
    
    logger.info(f"开始下载 {media_id}: {media_url}")
    
    # 设置适当的请求头
    if media_type == 'image':
        headers = youran.headers.img
        media_url=media_url[0]
    elif media_type == 'video':
        headers = youran.headers.video
        if 'oasis.video.weibocdn.com' in media_url:
            headers = youran.headers.mobile
    else:
        headers = youran.headers.mobile
    
    # 下载文件
    retries = 0
    while retries <= max_retries:
        try:
            # 使用youran的下载方法
            content = None
            if media_type == 'image':
                content = youran.net.img.download(media_url, progress=True, headers=headers, proxy=False)
            elif media_type == 'video':
                file_name = youran.net.video._extract_video_name(media_url)
                if file_name in media_url:
                    content = youran.net.BaseNet.download(media_url, progress=True, headers=youran.headers.video, proxy=False)
                else:
                    import urllib
                    redirected_url = urllib.request.urlopen(media_url).geturl()
                    content = youran.net.BaseNet.download(redirected_url, progress=True, headers=youran.headers.video, proxy=False)
            else:
                content = youran.net.BaseNet.download(media_url, progress=True, headers=headers, proxy=False)
            
            if content and len(content) > 0:
                logger.info(f"下载成功: {media_id}")
                return True, content
            else:
                logger.warning(f"下载内容为空: {media_id}")
        except Exception as e:
            logger.error(f"下载出错: {repr(e)}")
        
        # 重试
        retries += 1
        if retries <= max_retries:
            delay = random.randint(1, 5)
            logger.info(f"等待 {delay} 秒后重试 ({retries}/{max_retries})...")
            time.sleep(delay)
    
    logger.error(f"下载失败，已达到最大重试次数: {media_id}")
    return False, None

def save_to_minio(media, content):
    """
    将媒体内容保存到MinIO
    
    Args:
        media: 媒体记录
        content: 文件内容
        
    Returns:
        成功返回True，失败返回False
    """
    try:
        media_id = media['_id']
        media_type = media['media_type']
        media_url = media['media_url']
        
        # 根据媒体类型确定存储路径和文件名
        if media_type == 'image':
            storage_type = 'imgs'
            file_name = media_url[0].split('/')[-1]
        else:
            storage_type = 'videos'
            file_name = youran.net.video._extract_video_name(media_url)

        path = f"{storage_type}/{file_name}"
        logger.info(f"解析到媒体名字为: {file_name}")
        # 保存到MinIO
        min.save_weibo(path, content)
        logger.info(f"已上传到MinIO: {path}")
        return True
    except Exception as e:
        logger.error(f"保存到MinIO出错: {repr(e)}")
        return False
class WeiboSpider:
    def __init__(self, uid, max_pages=10, use_cookie=False, use_proxy=True, save_to_db=True, 
                 fetch_comments=True, fetch_retweets=True, comment_pages=3, max_retweet_depth=2,
                 download_media=False):
        """
        初始化爬虫
        
        Args:
            uid: 用户ID
            max_pages: 最大爬取页数
            use_cookie: 是否使用cookie
            use_proxy: 是否使用代理
            save_to_db: 是否保存到数据库
            fetch_comments: 是否爬取评论
            fetch_retweets: 是否爬取转发的微博
            comment_pages: 评论最大爬取页数
            max_retweet_depth: 转发微博的最大递归深度
            download_media: 是否立即下载媒体文件，False表示只保存URL
        """
        self.uid = str(uid)
        self.max_pages = max_pages
        self.use_cookie = use_cookie
        self.use_proxy = use_proxy
        self.save_to_db = save_to_db
        self.fetch_comments = fetch_comments
        self.fetch_retweets = fetch_retweets
        self.comment_pages = comment_pages
        self.max_retweet_depth = max_retweet_depth
        self.download_media = download_media
        self.since_id = None
        self.containerid = None
        self.total_blogs = 0
        self.crawled_blogs = 0
        self.crawled_comments = 0
        self.crawled_retweets = 0
        self.saved_media_urls = 0
        # 用于避免重复爬取转发微博
        self.processed_retweets = set()
        
    def _get_containerid(self):
        """获取用户的containerid"""
        try:
            # 第一个链接获取用户信息
            url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={self.uid}"
            response = youran.net.BaseNet.baseget(url, cookie=self.use_cookie, proxy=self.use_proxy)
            if not response:
                logger.error(f"获取用户信息失败: {self.uid}")
                return None
                
            data = json.loads(response)
            if data.get('ok') != 1:
                logger.error(f"API返回错误: {data.get('msg')}")
                return None
                
            # 提取containerid
            for tab in data['data']['tabsInfo']['tabs']:
                if tab['tab_type'] == 'weibo':
                    return tab['containerid']
            
            # 如果没有找到weibo标签，使用默认格式
            return f"107603{self.uid}"
            
        except Exception as e:
            logger.error(f"获取containerid时出错: {repr(e)}")
            return f"107603{self.uid}"  # 使用默认格式
            
    def get_user_info(self):
        """获取用户信息"""
        logger.info(f"开始获取用户 {self.uid} 的信息")
        user_info = youran.db.user.find_users([self.uid])
        
        if user_info and len(user_info) > 0:
            logger.info(f"从数据库获取到用户信息: {user_info[0]['screen_name']}")
            return user_info[0]
            
        logger.info(f"数据库中无用户信息，从网络获取")
        user_info = youran.net.user.get(self.uid)
        
        if not user_info:
            logger.error(f"获取用户信息失败: {self.uid}")
            return None
            
        if self.save_to_db:
            youran.db.user.add(user_info)
            logger.info(f"已保存用户信息到数据库: {user_info['screen_name']}")
            
        return user_info
        
    def fetch_page(self, page=1):
        """
        获取指定页的微博
        
        Args:
            page: 页码
            
        Returns:
            (is_success, weibo_list, since_id)
        """
        if not self.containerid:
            self.containerid = self._get_containerid()
            if not self.containerid:
                return False, [], None
                
        # 构建请求URL
        url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={self.uid}&containerid={self.containerid}"
        
        # 添加翻页参数
        if self.since_id and page > 1:
            url += f"&since_id={self.since_id}"
        elif page > 1:
            logger.warning(f"没有since_id，无法获取第{page}页")
            return False, [], None
            
        logger.info(f"开始获取第{page}页: {url}")
        
        # 发送请求
        response = youran.net.BaseNet.baseget(url, cookie=self.use_cookie, proxy=self.use_proxy)
        if not response:
            logger.error(f"获取第{page}页失败")
            return False, [], None
            
        try:
            data = json.loads(response)
            if data.get('ok') != 1:
                logger.error(f"API返回错误: {data.get('msg')}")
                return False, [], None
                
            cards = data['data']['cards']
            weibos = []
            
            # 提取微博列表
            for card in cards:
                if card.get('card_type') == 9 and 'mblog' in card:
                    weibos.append(card['mblog'])
                    
            # 获取下一页的since_id
            next_since_id = None
            if 'cardlistInfo' in data['data'] and 'since_id' in data['data']['cardlistInfo']:
                next_since_id = data['data']['cardlistInfo']['since_id']
                
            logger.info(f"第{page}页获取成功，共{len(weibos)}条微博")
            return True, weibos, next_since_id
            
        except Exception as e:
            logger.error(f"解析第{page}页数据时出错: {repr(e)}")
            return False, [], None
            
    def extract_media_urls(self, weibo):
        """
        提取微博中的媒体URL并保存到数据库
        
        Args:
            weibo: 微博数据
            
        Returns:
            提取的媒体URL数量
        """
        try:
            if not self.save_to_db:
                return 0
                
            media_count = 0
            bid = weibo.get('bid', weibo.get('mblogid', ''))
            
            # 提取图片URL
            pic_urls = []
            if 'pic_ids' in weibo and weibo['pic_ids']:
                for pic_id in weibo['pic_ids']:
                    pic_info = None
                    if 'pic_infos' in weibo and pic_id in weibo['pic_infos']:
                        pic_info = weibo['pic_infos'][pic_id]
                        
                    if pic_info:
                        # 优先使用large尺寸的图片
                        if 'large' in pic_info:
                            pic_urls.append({
                                'url': pic_info['large']['url'],
                                'type': 'image',
                                'width': pic_info['large'].get('width', 0),
                                'height': pic_info['large'].get('height', 0)
                            })
                        elif 'original' in pic_info:
                            pic_urls.append({
                                'url': pic_info['original']['url'],
                                'type': 'image',
                                'width': pic_info['original'].get('width', 0),
                                'height': pic_info['original'].get('height', 0)
                            })
            
            # 提取视频URL
            video_urls = []
            if 'page_info' in weibo and weibo['page_info'].get('type') == 'video':
                video_info = weibo['page_info']
                if 'media_info' in video_info:
                    # 可能有多种分辨率，优先使用高分辨率
                    media_info = video_info['media_info']
                    if 'stream_url_hd' in media_info and media_info['stream_url_hd']:
                        video_urls.append({
                            'url': media_info['stream_url_hd'],
                            'type': 'video',
                            'duration': media_info.get('duration', 0)
                        })
                    elif 'stream_url' in media_info and media_info['stream_url']:
                        video_urls.append({
                            'url': media_info['stream_url'],
                            'type': 'video',
                            'duration': media_info.get('duration', 0)
                        })
            
            # 合并所有媒体URL
            all_media = pic_urls + video_urls
            media_count = len(all_media)
            
            if media_count > 0:
                # 将URL保存到数据库
                for media in all_media:
                    media_doc = {
                        '_id': f"{bid}_{self.saved_media_urls}",
                        'bid': bid,
                        'uid': self.uid,
                        'media_url': media['url'],
                        'media_type': media['type'],
                        'create_time': weibo.get('created_at1', time.time()),
                        'add_time': time.time(),
                        'download_status': 'pending',  # pending, success, failed
                        'retry_count': 0,
                        'metadata': media
                    }
                    try:
                        # 使用media_urls类而不是直接访问集合
                        if media_doc['media_type'] == "video":
                            SUCCESS,content = download_media(media_doc)
                            if SUCCESS:
                                save_to_minio(media_doc,content)
                        else:
                            youran.db.media_urls.add(media_doc)
                        self.saved_media_urls += 1
                    except Exception as e:
                        logger.warning(f"保存媒体URL出错: {repr(e)}")
            
            logger.debug(f"从微博 {bid} 中提取了 {media_count} 个媒体URL")
            return media_count
            
        except Exception as e:
            logger.error(f"提取媒体URL时出错: {repr(e)}")
            return 0
            
    def extract_comment_media_urls(self, comments_data):
        """
        提取评论中的图片URL并保存到数据库
        
        Args:
            comments_data: 评论数据
            
        Returns:
            提取的图片URL数量
        """
        try:
            if not self.save_to_db or not comments_data or 'data' not in comments_data:
                return 0
                
            pic_count = 0
            mid = comments_data.get('mid', '')
            
            # 提取评论中的图片
            img_urls = youran.net.comment.extract_img(comments_data)
            if not img_urls:
                return 0
                
            for i, url in enumerate(img_urls):
                media_doc = {
                    '_id': f"comment_{mid}_{i}",
                    'bid': f"comment_{mid}",
                    'uid': self.uid,
                    'media_url': url,
                    'media_type': 'image',
                    'create_time': time.time(),
                    'add_time': time.time(),
                    'download_status': 'pending',
                    'retry_count': 0,
                    'source': 'comment',
                    'metadata': {'url': url}
                }
                try:
                    # 使用media_urls类而不是直接访问集合
                    youran.db.media_urls.add(media_doc)
                    pic_count += 1
                except Exception as e:
                    logger.warning(f"保存评论图片URL出错: {repr(e)}")
            
            logger.debug(f"从评论中提取了 {pic_count} 张图片URL")
            return pic_count
            
        except Exception as e:
            logger.error(f"提取评论图片URL时出错: {repr(e)}")
            return 0

    def _fetch_comments(self, weibo, max_pages=1):
        """
        获取微博评论
        
        Args:
            weibo: 微博数据
            max_pages: 最大爬取页数
            
        Returns:
            成功爬取的评论数量
        """
        if not self.fetch_comments:
            return 0
            
        mid = weibo.get('mid')
        if not mid:
            logger.warning(f"微博缺少mid，无法获取评论")
            return 0
            
        logger.info(f"开始获取微博 {mid} 的评论")
        comment_count = 0
        max_id = None
        
        for page in range(1, 2):
            try:
                logger.debug(f"获取评论第{page}页，max_id={max_id}")
                
                # 获取评论
                comments_data = youran.net.comment.get(
                    weibo, 
                    maxid=max_id, 
                    cookie=False, 
                    proxy=False
                )
                
                if not comments_data or 'data' not in comments_data:
                    logger.warning(f"获取评论第{page}页失败或无评论")
                    break
                    
                # 保存评论到数据库
                if self.save_to_db:
                    youran.db.comment.add(comments_data)
                    
                comment_count += len(comments_data['data'].get('data', []))
                logger.info(f"已获取 {comment_count} 条评论")
                
                # 提取评论中的图片URL
                if self.save_to_db:
                    self.extract_comment_media_urls(comments_data)
                    
                # 获取下一页评论的max_id
                if 'max_id' in comments_data['data'] and comments_data['data']['max_id'] != 0:
                    max_id = comments_data['data']['max_id']
                    # 随机延时，避免被反爬
                    delay = random.randint(1, 3)
                    time.sleep(delay)
                else:
                    logger.info(f"没有更多评论")
                    break
                    
            except Exception as e:
                logger.error(f"获取评论时出错: {repr(e)}")
                break
                
        logger.info(f"微博 {mid} 共获取 {comment_count} 条评论")
        return comment_count
        
    def process_retweet(self, retweet_data, depth=0):
        """
        处理转发的微博
        
        Args:
            retweet_data: 转发微博数据
            depth: 当前递归深度
            
        Returns:
            是否成功处理
        """
        if not self.fetch_retweets or depth >= self.max_retweet_depth:
            return False
            
        if not retweet_data:
            return False
            
        bid = retweet_data.get('bid')
        if not bid:
            return False
            
        # 避免重复爬取
        if bid in self.processed_retweets:
            logger.debug(f"转发微博 {bid} 已处理过，跳过")
            return True
            
        self.processed_retweets.add(bid)
        
        try:
            logger.info(f"开始处理转发微博: {bid} (深度: {depth})")
            
            # 获取完整微博内容
            full_retweet = youran.net.mblog.get(
                {'bid': bid, 'isLongText': True}, 
                cookie=self.use_cookie, 
                proxy=self.use_proxy
            )
            
            if not full_retweet:
                logger.warning(f"获取转发微博 {bid} 详情失败")
                return False
                
            # 处理微博内容
            if self.process_weibo(full_retweet, 0):
                self.crawled_retweets += 1
                
            return True
            
        except Exception as e:
            logger.error(f"处理转发微博时出错: {repr(e)}")
            return False
            
    def process_weibo(self, weibo, current_page):
        """处理单条微博"""
        try:
            if not weibo:
                return False
                
            # 添加uid字段
            weibo['uid'] = int(self.uid)
            
            # 计算创建时间时间戳
            try:
                created_time = datetime.strptime(weibo['created_at'], "%a %b %d %H:%M:%S %z %Y")
                weibo['created_at1'] = created_time.timestamp()
            except Exception as e:
                logger.error(f"解析创建时间失败: {repr(e)}")
                weibo['created_at1'] = time.time()
                
            # 添加爬取时间
            weibo['spider_time'] = time.time()
            if 'mblogid' in weibo: #兼容mblogid和bid
                weibo['bid']=weibo['mblogid']
            # 保存微博到数据库
            if self.save_to_db:
                bid = weibo.get('bid', weibo.get('mblogid', ''))
                
                # 检查是否已存在
                if youran.db.mblog.exists({'bid': bid}):
                    logger.info(f"微博已存在: {bid}")
                    return True
                    
                # 将mid作为_id
                weibo['_id'] = weibo.get('mid', '')
                weibo['id'] = weibo.get('mid', '')
                # 保存到数据库
                result = youran.db.mblog.add(weibo)
                if not result:
                    logger.error(f"保存微博失败: {bid}")
                    return False
                    
                logger.info(f"已保存微博: {bid}")
                
            # 提取媒体URL
            self.extract_media_urls(weibo)
            
            
            # 爬取评论
            if self.fetch_comments:
                comment_count = self._fetch_comments(weibo, self.comment_pages)
                self.crawled_comments += comment_count
                
            # 处理转发的微博
            if self.fetch_retweets and 'retweeted_status' in weibo:
                logger.debug(f"发现转发微博: {weibo.get('bid', '')}")
                self.process_retweet(weibo['retweeted_status'], 0)
                
            return True
            
        except Exception as e:
            logger.error(f"处理微博时出错: {repr(e)}")
            return False
            
            
    def start(self):
        """开始爬取"""
        # 获取用户信息
        user_info = self.get_user_info()
        if not user_info:
            logger.error("无法获取用户信息，爬取终止")
            return False
            
        username = user_info.get('screen_name', self.uid)
        logger.info(f"开始爬取用户 {username} 的微博")
        
        page = 1
        while page <= self.max_pages:
            # 获取当前页微博
            success, weibos, next_since_id = self.fetch_page(page)
            
            if not success or not weibos:
                logger.warning(f"第{page}页获取失败或无内容，爬取结束")
                break
                
            # 处理本页微博
            for weibo in weibos:
                if self.process_weibo(weibo, page):
                    self.crawled_blogs += 1
                    
            # 输出进度
            logger.info(f"已爬取 {self.crawled_blogs} 条微博, {self.crawled_comments} 条评论, {self.crawled_retweets} 条转发微博")
            
            # 保存下一页的since_id
            self.since_id = next_since_id
            
            # 如果没有since_id，说明已到最后一页
            if not next_since_id:
                logger.warning(f"无下一页since_id，爬取结束")
                break
                
            # 随机延时，避免被反爬
            delay = random.randint(3, 10)
            logger.info(f"等待 {delay} 秒后继续爬取下一页")
            time.sleep(delay)
            
            page += 1
            
        logger.info(f"爬取完成，共爬取 {self.crawled_blogs} 条微博, {self.crawled_comments} 条评论, {self.crawled_retweets} 条转发微博")
        return True

def get_random_users(count=20, source="follow"):
    """
    从数据库中获取随机用户ID
    
    Args:
        count: 获取用户数量
        source: 来源表，可以是"follow"、"user"或"comment"
        
    Returns:
        用户ID列表
    """
    logger.info(f"从数据库获取 {count} 个随机用户，来源: {source}")
    
    ids = set()
    try:
        if source == "follow":
            # 从关注列表中获取
            for item in youran.db.follow.random(count * 2):  # 多获取一些，防止过滤后不够
                if 'blogger' in item:
                    ids.add(item['blogger'])
                if len(ids) >= count:
                    break
        elif source == "user":
            # 从用户表中获取
            for user in youran.db.user.random(count * 2):
                if 'id' in user:
                    ids.add(user['id'])
                if len(ids) >= count:
                    break
        elif source == "comment":
            # 从评论中获取用户
            comments = youran.db.comment.random(count * 5)  # 获取更多评论，因为一个评论可能有多个用户
            for comment in comments:
                if 'data' in comment:
                    if 'data' in comment['data']:
                        for item in comment['data']['data']:
                            if 'user' in item and 'id' in item['user']:
                                ids.add(item['user']['id'])
                                if len(ids) >= count:
                                    break
    except Exception as e:
        logger.error(f"获取随机用户时出错: {repr(e)}")
    
    # 确保返回指定数量的用户ID
    ids_list = list(ids)
    if len(ids_list) > count:
        ids_list = random.sample(ids_list, count)
    
    logger.info(f"成功获取 {len(ids_list)} 个随机用户")
    return ids_list

def batch_crawl_users(user_ids, args):
    """
    批量爬取用户微博
    
    Args:
        user_ids: 用户ID列表
        args: 命令行参数
        
    Returns:
        成功爬取的用户数量
    """
    logger.info(f"开始批量爬取 {len(user_ids)} 个用户的微博")
    
    success_count = 0
    total_blogs = 0
    total_comments = 0
    total_retweets = 0
    
    for i, uid in enumerate(user_ids):
        logger.info(f"[{i+1}/{len(user_ids)}] 爬取用户 {uid}")
        
        spider = WeiboSpider(
            uid=uid,
            max_pages=args.pages,
            use_cookie=not args.no_cookie,
            use_proxy=not args.no_proxy,
            save_to_db=not args.no_save,
            fetch_comments=not args.no_comments,
            fetch_retweets=not args.no_retweets,
            comment_pages=args.comment_pages,
            max_retweet_depth=args.retweet_depth,
            download_media=args.download_media
        )
        
        try:
            result = spider.start()
            if result:
                success_count += 1
                total_blogs += spider.crawled_blogs
                total_comments += spider.crawled_comments
                total_retweets += spider.crawled_retweets
                
            # 用户间的延时，避免被反爬
            if i < len(user_ids) - 1:
                delay = random.randint(10, 30)
                logger.info(f"等待 {delay} 秒后继续爬取下一个用户")
                time.sleep(delay)
                
        except Exception as e:
            logger.error(f"爬取用户 {uid} 时出错: {repr(e)}", exc_info=True)
    
    logger.info(f"批量爬取完成，成功爬取 {success_count}/{len(user_ids)} 个用户")
    logger.info(f"总计爬取 {total_blogs} 条微博, {total_comments} 条评论, {total_retweets} 条转发微博")
    
    return success_count

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="爬取指定用户的微博")
    parser.add_argument("uid", nargs='?', help="用户ID，不指定时使用随机模式")
    parser.add_argument("--random", action="store_true", help="随机选择用户爬取")
    parser.add_argument("--random-count", type=int, default=10, help="随机爬取的用户数量")
    parser.add_argument("--random-source", choices=["follow", "user", "comment"], default="user", help="随机用户的来源")
    parser.add_argument("--pages", type=int, default=10, help="每个用户最大爬取页数")
    parser.add_argument("--no-cookie", action="store_true", help="不使用cookie")
    parser.add_argument("--no-proxy", action="store_true", help="不使用代理")
    parser.add_argument("--no-save", action="store_true", help="不保存到数据库")
    parser.add_argument("--no-comments", action="store_true", help="不爬取评论")
    parser.add_argument("--no-retweets", action="store_true", help="不爬取转发微博")
    parser.add_argument("--comment-pages", type=int, default=3, help="评论最大爬取页数")
    parser.add_argument("--retweet-depth", type=int, default=2, help="转发微博的最大递归深度")
    parser.add_argument("--download-media", action="store_true", help="立即下载媒体文件（而不是仅保存URL）")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="日志级别")
    parser.add_argument("--log-file", default="weibo_spider.log", help="日志文件名")
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = getattr(logging, args.log_level)
    global logger
    logger = setup_logger(log_file=args.log_file, level=log_level)
    
    logger.info(f"=== 开始运行 Weibo Spider ===")
    
    try:
        # 随机模式
        if args.random or args.uid is None:
            random_batch_count = 0
            while True:
                random_batch_count += 1
                logger.info(f"使用随机模式，爬取 {args.random_count} 个随机用户，第 {random_batch_count} 批")
                user_ids = get_random_users(args.random_count, args.random_source)
                if not user_ids:
                    logger.error("获取随机用户失败，程序终止")
                    return
                    
                batch_crawl_users(user_ids, args)
            
        # 指定用户ID模式
        else:
            logger.info(f"爬取指定用户: {args.uid}")
            logger.info(f"最大爬取页数: {args.pages}")
            logger.info(f"使用Cookie: {not args.no_cookie}")
            logger.info(f"使用代理: {not args.no_proxy}")
            logger.info(f"保存到数据库: {not args.no_save}")
            logger.info(f"爬取评论: {not args.no_comments}")
            logger.info(f"爬取转发微博: {not args.no_retweets}")
            logger.info(f"评论最大爬取页数: {args.comment_pages}")
            logger.info(f"转发微博最大递归深度: {args.retweet_depth}")
            logger.info(f"立即下载媒体: {args.download_media}")
            
            spider = WeiboSpider(
                uid=args.uid,
                max_pages=args.pages,
                use_cookie=not args.no_cookie,
                use_proxy=not args.no_proxy,
                save_to_db=not args.no_save,
                fetch_comments=not args.no_comments,
                fetch_retweets=not args.no_retweets,
                comment_pages=args.comment_pages,
                max_retweet_depth=args.retweet_depth,
                download_media=args.download_media
            )
            
            result = spider.start()
            status = "成功" if result else "失败"
            logger.info(f"爬取{status}，共爬取 {spider.crawled_blogs} 条微博, {spider.crawled_comments} 条评论, {spider.crawled_retweets} 条转发微博, 保存 {spider.saved_media_urls} 个媒体URL")
            
    except KeyboardInterrupt:
        logger.warning("用户中断爬取")
    except Exception as e:
        logger.error(f"爬取过程中发生错误: {repr(e)}", exc_info=True)
    finally:
        logger.info("=== 爬虫运行结束 ===")

if __name__ == "__main__":
    # 示例用法
    # python test_get_user_mblog.py 3164402322 --pages 5
    # python test_get_user_mblog.py --random --random-count 5
    # python test_get_user_mblog.py --random --random-source comment --random-count 10
    main()

