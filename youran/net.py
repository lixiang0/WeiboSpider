import json
# from . import headers
# from . import db
import youran
from youran import headers
import requests,tqdm,io,re
from scrapy.selector import Selector
import urllib
import socket
import time
import requests.packages.urllib3.util.connection as urllib3_cn
from requests.exceptions import RequestException, Timeout, ConnectionError

import youran.headers

def allowed_gai_family():
    family = socket.AF_INET # force IPv4
    return family
urllib3_cn.allowed_gai_family = allowed_gai_family

class BaseNet():
    @staticmethod
    def baseget(url, cookie=False, headers=youran.headers.mobile, proxy=True, max_retries=1, retry_delay=2):
        """
        发送GET请求并支持重试机制
        
        Args:
            url: 请求URL
            cookie: 是否使用cookie
            headers: 请求头
            proxy: 是否使用代理
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)
            
        Returns:
            响应文本或None(如果所有重试都失败)
        """
        cookies = youran.headers.cookies if cookie else None
        _proxies = youran.db.proxy.get_randomip() if proxy else None
        youran.logger.warning(f'获取代理地址:{_proxies}')
        
        for attempt in range(max_retries):
            try:
                r = requests.get(
                    url, 
                    headers=headers,
                    cookies=cookies,
                    verify=False,
                    proxies=_proxies,
                    timeout=30
                )
                r.raise_for_status()  # 抛出HTTP错误状态码的异常
                return r.text
            except Timeout as e:
                youran.logger.warning(f"请求超时 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            except ConnectionError as e:
                youran.logger.warning(f"连接错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                # 如果是代理问题，尝试获取新代理
                if proxy:
                    _proxies = youran.db.proxy.get_randomip()
                    youran.logger.warning(f'重新获取代理地址:{_proxies}')
            except RequestException as e:
                youran.logger.warning(f"请求异常 (尝试 {attempt+1}/{max_retries}): {str(e)}")
            
            # 最后一次尝试失败
            if attempt == max_retries - 1:
                youran.logger.error(f"所有重试都失败: {url}")
                return None
                
            # 延迟重试，使用指数退避策略
            delay = retry_delay * (2 ** attempt)
            youran.logger.warning(f"等待 {delay} 秒后重试...")
            time.sleep(delay)

    @staticmethod
    def download(url, progress=False, headers=youran.headers.mobile, proxy=False, max_retries=3, retry_delay=2):
        """改进的下载方法，支持重试机制"""
        for attempt in range(max_retries):
            try:
                _proxies = youran.db.proxy.get_randomip() if proxy else None
                response = requests.get(
                    url, 
                    headers=headers, 
                    stream=True,
                    timeout=30,
                    verify=False,
                    proxies=_proxies
                )
                response.raise_for_status()
                
                if response.status_code != 200:
                    youran.logger.warning(f"非200状态码: {response.status_code}")
                    continue
                    
                if 'Content-length' not in response.headers:
                    youran.logger.warning("响应中没有Content-length头")
                    continue
                    
                file_size = response.headers['Content-length']
                pbar = None
                if progress:
                    pbar = tqdm.tqdm(total=int(file_size), unit='B', unit_scale=True, desc=url.split('/')[-1][:20])
                    
                with io.BytesIO() as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                            if progress and pbar:
                                pbar.update(1024)
                    if progress and pbar:
                        pbar.close()
                    return f.getvalue()
                    
            except (RequestException, IOError) as e:
                youran.logger.warning(f"下载失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                
                # 如果是代理问题，尝试获取新代理
                if proxy and isinstance(e, ConnectionError):
                    _proxies = youran.db.proxy.get_randomip()
                
                # 最后一次尝试失败
                if attempt == max_retries - 1:
                    youran.logger.error(f"所有下载重试都失败: {url}")
                    return None
                    
                # 延迟重试
                delay = retry_delay * (2 ** attempt)
                youran.logger.warning(f"等待 {delay} 秒后重试下载...")
                time.sleep(delay)
        
        return None

class Comment(BaseNet):
    
    def get(self, mblog, maxid=None, cookie=False, proxy=False):
        mid = mblog['mid']
        comment_url = f'https://m.weibo.cn/comments/hotflow?id={mid}&mid={mid}'
        comment_url = comment_url+f'&max_id={maxid}' if maxid else comment_url
        try:
            res = self.baseget(comment_url, cookie=cookie, proxy=proxy)
            if res is None:
                youran.logger.warning(f"获取评论失败: {mid}")
                return None
                
            if '微博-出错了' in res:
                youran.logger.warning(f"微博返回错误页面: {mid}")
                return None
                
            comments = json.loads(res)
            comments['mid'] = mid
            comments['_id'] = mid
            return comments
        except json.JSONDecodeError as e:
            youran.logger.warning(f"JSON解析错误: {str(e)}")
            return None
        except Exception as e:
            youran.logger.warning(f"获取评论异常: {repr(e)}")
            return None  # 网络错误

    def extract_img(self,comments):
        urls_name=[]
        if 'data' in comments.keys():
            pics=comments['data']['data']
            if len(pics)>0:
                for pic in pics:
                    # print(pic)
                    if 'pic' in pic.keys():
                        name=pic['pic']['pid']
                        img_url=pic['pic']['large']['url']
                        urls_name.append((img_url,name))
                # return urls_name
        return urls_name

class Follow(BaseNet):
    def get(self,uid, page=1,proxy=False,cookie=False):
        follows_url = f'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_{uid}_-_1042015:tagCategory_019'
        next_url = follows_url+f'&page={page}' if page > 1 else follows_url
        res = self.baseget(next_url,proxy=proxy,cookie=cookie)
        obj = json.loads(res)
        # print(follows_url,obj)
        if obj['ok'] == 1:
            users=[]
            cards = obj['data']['cards']
            total = obj['data']['cardlistInfo']['total']
            # print(total)
            for card in cards:
                for item in card['card_group']:
                    # print(item)
                    if 'user' in item.keys():
                        user = item['user']
                        if user is None:
                            return None,None
                        user['_id'] = user['id']
                        users.append(user)
            return total,users
        return None,None

class Hot(BaseNet):
    def get(self):
        hot_url='https://www.weibo.com/a/hot/realtime?display=0&retcode=6102'
        # hot_url='https://weibo.com/a/hot/realtime?display=0&retcode=6102'
        hot_text_response = self.baseget(hot_url,cookie=True)
        # print(hot_text_response)
        lists=Selector(text=hot_text_response).xpath('//div[@node-type="feed_list"]').xpath('//div[@action-type="feed_list_item"]').getall()
        if len(lists)==0:
            return None
        results=[]
        items=[]
        for li in lists:
            text=Selector(text=li).xpath('//a[@class="S_txt1"]/text()').get()
            href=Selector(text=li).xpath('//a[@class="S_txt1"]').attrib['href']
            results.append((text,href))
        return results
    def get_detail(self,url):
        # print(url)
        url='https://weibo.com/a/hot/'+url+'&display=0&retcode=6102' if '/a/hot/' not in url else 'https://weibo.com'+url
        detail_response=self.baseget(url,cookie=True)
        # print(detail_response)
        lists=Selector(text=detail_response).xpath('//div[@node-type="feed_list"]').xpath('//div[@action-type="feed_list_item"]').getall()
        # print(url,lists)
        if len(lists)==0:
            return url,None
        bids=[]
        for li in lists:
            _=Selector(text=li).xpath('//div[@href]').attrib['href']
            _=re.findall('[0-9]+/[0-9a-z-A-z]+',_)
            bid=_[0].split('/')[-1] if len(_)==1 else None
            if bid is None:
                continue
            bids.append(bid)
        # print(detail_response)
        return url,bids

    def extract_img(self,comments):
        urls_name=[]
        if 'data' in comments.keys():
            pics=comments['data']['data']
            if len(pics)>0:
                for pic in pics:
                    # print(pic)
                    if 'pic' in pic.keys():
                        name=pic['pic']['pid']
                        img_url=pic['pic']['large']['url']
                        urls_name.append((img_url,name))
                # return urls_name
        return urls_name

class Mblog(BaseNet):
    # different user return different item for every page
    # https://weibo.com/ajax/statuses/mymblog?uid=2014433131&page=1238
    # def extract_mblogs1(self,uid, page=1,cookie=False,proxy=False):
    #     # page_url=f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0'
    #     # 1663072851
    #     next_url=f'https://m.weibo.cn/api/container/getIndex?containerid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page={page}'
    #     # next_url = f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}'
    #     obj=None
    #     try:
    #         print('next_url:',next_url)
    #         res = self.baseget(next_url,cookie=cookie,proxy=proxy)
    #         print(res)
    #         if '100005' in res:
    #             return -2,'请求过于频繁' #请求过于频繁
    #         obj=json.loads(res)
    #     except Exception as e:
    #         return -3,repr(e) #网络错误
    #     mblogs = []
    #     if obj['ok'] == 1:
    #         for card in obj['data']['cards']:
    #             if card['card_type']==9:
    #                 mblogs.append(card['mblog']) 
    #     else:
    #         return -1,obj #可能需要重新登录
    #     return 0, mblogs
    def extract_mblogs(self,uid, page=1,cookie=False,proxy=False):
        # page_url=f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0'
        next_url = f'https://m.weibo.cn/api/container/getIndex?uid={uid}&lfid=2304136390144374_-_WEIBO_SECOND_PROFILE_WEIBO&containerid=107603{uid}&page={page}'
        obj=None
        try:
            # print('next_url:',next_url)
            res = self.baseget(next_url,cookie=cookie,proxy=proxy)
            # print(res)
            if '100005' in res:
                return -2,'请求过于频繁' #请求过于频繁
            obj=json.loads(res)
        except Exception as e:
            return -3,repr(e) #网络错误
        # print(res)
        total_mblogs = 0
        mblogs = []
        if obj['ok'] == 1:
            cards = obj['data']['cards']
            total_mblogs = obj['data']['cardlistInfo']['total']
            for card in cards:
                # print(card)
                if not 'mblog' in card:
                    continue
                mblog = card['mblog']
                # mblog.pop('user')
                mblogs.append(mblog)

        else:
            return -1,obj['msg'] #可能需要重新登录
        return total_mblogs, mblogs

    # https://m.weibo.cn/feed/friends?max_id=4589611853288529:
    def extract_feeds(self,maxbid=None):
        page_url = f'https://m.weibo.cn/feed/friends'
        if maxbid is not None:
            page_url+=f'?max_id={maxbid}'
        res = self.baseget(page_url,cookie=True)
        if '请求过于频繁,歇歇吧' in res:
            return -1, -1
        obj = json.loads(res)
        print(page_url)
        max_bid=obj['data']['max_id']
        mblogs = []
        if obj['ok'] == 1:
            cards = obj['data']['statuses']
            for card in cards:
                # print(card)

                # mblog.pop('user')
                mblogs.append(card)
        else:
            return -1,-1
        return max_bid, mblogs

    def get(self,mblog,cookie=False,proxy=False):
        # 对于长微博需要跳转具体微博，才能查看全部内容
        # https://m.weibo.cn/detail/{mid}
        # https://m.weibo.cn/status/{bid}
        mid = mblog['bid']
        res = mblog
        # print(res)
        if 'isLongText' in mblog and mblog['isLongText']:
            long_text_url = 'https://m.weibo.cn/status/'+str(mid)
            long_text_response= None
            try:
                long_text_response= self.baseget(long_text_url,cookie=cookie,proxy=proxy)
            except Exception as e:
                return None
            res = re.compile(
                r'var\ \$render_data = \[\{.*\}\]\[0\]\ \|\|\ \{\};', re.DOTALL).findall(long_text_response)
            if len(res) < 1:
                return None
            res = json.loads(str(res[0].replace('\n', '')[20:-11]))['status']
        res['_id'] = res['mid']
        return res
class User(BaseNet):
    def get(self,id):
        url=f'https://m.weibo.cn/api/container/getIndex?uid={id}&t=0&luicode=10000011&lfid=100103type%3D3%26q%3D{id}%26t%3D0&containerid=100505{id}'
        # url=f'https://m.weibo.cn/profile/info?uid={id}'
        res = self.baseget(url)
        if '用户不存在' in res:
            return None
        # print(res)
        obj = json.loads(res)
        if obj['ok'] == 1:
            user = obj['data']['userInfo']
            user['_id'] = id
            return user
        else:
            return None

class Video(BaseNet):
    def __init__(self):
        super().__init__()
        # 预编译正则表达式以提高性能
        self.regex_patterns = {
            'miaopai_expires': re.compile(r'.*?Expires'),
            'miaopai_mp4': re.compile(r'.*.mp4\?'),
            'sina_video': re.compile(r'n/(.*).(mp4|m3u8)\?'),
            'edge_video': re.compile(r'/(.*).mp4'),
            'meitu_video': re.compile(r'm/(.*).(mp4|m3u8)'),
            'oasis_video': re.compile(r'o2/(.*).(mp4|m3u8)'),
            'f_video': re.compile(r'(u0|o0)/(.*).(mp4|m3u8)\?label'),
            'tencent_video': re.compile(r'v\.qq\.com/.*?/(.*?)(\.mp4|\.m3u8)'),
            'default_mp4': re.compile(r'.*.mp4\?')
        }
        
    def _safe_regex_find(self, pattern_name, text):
        """安全地应用正则表达式，避免异常"""
        try:
            pattern = self.regex_patterns.get(pattern_name)
            if not pattern:
                youran.logger.error(f"未找到正则表达式模式: {pattern_name}")
                return None
                
            result = pattern.findall(text)
            return result if result else None
        except Exception as e:
            youran.logger.error(f"正则表达式匹配失败 {pattern_name}: {repr(e)}")
            return None
    
    def extract(self, mblog):
        """提取微博中的视频URL和文件名"""
        if not mblog:
            youran.logger.warning("输入为空")
            return None, None
            
        try:
            # 检查必要的键
            page_info = mblog.get('page_info')
            if not page_info:
                youran.logger.warning(f"缺少page_info: {mblog}")
                return None, None
                
            if page_info.get('type') != 'video':
                youran.logger.warning(f"page_info类型不是视频: {page_info.get('type')}")
                return None, None
                
            # 获取视频信息
            media_info = page_info.get('media_info')
            if not media_info:
                youran.logger.warning(f"未找到视频信息: {page_info}")
                return None, None
                
            video_url = media_info.get('stream_url', '')
            if not video_url:
                youran.logger.warning(f"视频链接为空")
                return None, None
                
            youran.logger.warning(f"解析到视频链接：{video_url}")
            video_name = self._extract_video_name(video_url)
            
            if video_name:
                return video_url, video_name
            else:
                youran.logger.warning(f"未能提取视频名称: {video_url}")
                return None, None
                
        except Exception as e:
            youran.logger.error(f"视频提取过程中发生错误: {repr(e)}")
            return None, None
            
    def _extract_video_name(self, video_url):
        """根据URL提取视频名称"""
        try:
            # CDN视频
            if any(domain in video_url for domain in ['cntv.vod.cdn.myqcloud.com', 'flv.bn.netease.com']):
                return video_url.split('/')[-1]
                
            # 秒拍视频
            elif 'miaopai.video.weibocdn.com' in video_url:
                if '?Expires=' in video_url:
                    result = self._safe_regex_find('miaopai_expires', video_url)
                    if result and result[0]:
                        return result[0].split('/')[-1][:-8] + '.mp4'
                if '.mp4?label=mp4_hd' in video_url:
                    result = self._safe_regex_find('miaopai_mp4', video_url)
                    if result and result[0]:
                        return result[0][:-1].split('/')[-1]   
            # 新浪视频API (需要重定向)
            elif 'api.ivideo.sina.com.cn' in video_url:
                try:
                    redirected_url = urllib.request.urlopen(video_url).geturl()
                    result = self._safe_regex_find('sina_video', redirected_url)
                    if result and result[0]:
                        return result[0][0] + '.' + result[0][1]
                except Exception as e:
                    youran.logger.error(f"处理重定向URL时出错: {repr(e)}")
            elif 'redirect_tencent_video' in video_url:
                try:
                    redirected_url = urllib.request.urlopen(video_url).geturl()
                    result = self._safe_regex_find('tencent_video', redirected_url)
                    if result and result[0]:
                        return result[0][0] + '.' + result[0][1]
                except Exception as e:
                    youran.logger.error(f"处理重定向URL时出错: {repr(e)}")                  
            # 新浪图片服务器视频
            elif 'https://us.sinaimg.cn' in video_url:
                result = self._safe_regex_find('sina_video', video_url)
                if result and result[0]:
                    return result[0][0] + '.' + result[0][1]
                    
            # 优酷视频
            elif 'https://api.youku.com' in video_url:
                return video_url.split('data=')[1] + '.mp4'
                
            # 新浪边缘服务器视频
            elif 'edge.ivideo.sina.com.cn' in video_url:
                result = self._safe_regex_find('edge_video', video_url)
                if result and result[0]:
                    return result[0] + '.mp4'
                    
            # 美图视频
            elif 'http://mvvideo2.meitudata.com' in video_url:
                result = self._safe_regex_find('meitu_video', video_url)
                if result and result[0]:
                    return result[0][0] + '.' + result[0][1]
                    
            # 绿洲视频
            elif 'https://oasis.video.weibocdn.com' in video_url:
                result = self._safe_regex_find('oasis_video', video_url)
                if result and result[0]:
                    return result[0][0] + '.' + result[0][1]
                    
            # 微博CDN视频
            elif 'https://f.video.weibocdn.com' in video_url:
                result = self._safe_regex_find('f_video', video_url)
                if result and result[0]:
                    return result[0][1] + '.' + result[0][2]
                    
            # 默认情况
            else:
                result = self._safe_regex_find('default_mp4', video_url.split('/')[-1])
                if result and result[0]:
                    return result[0][:-1]
                    
            # 如果所有方法失败，返回通用名称
            return f"video_{int(time.time())}.mp4"
            
        except Exception as e:
            youran.logger.error(f"提取视频名称时出错: {repr(e)}")
            return f"error_video_{int(time.time())}.mp4"

class Img(BaseNet):
    def extract(self,mblog):
        url_names = []
        if 'pics' in mblog.keys():
            pics = [pic['large']['url'] for pic in mblog['pics']]
            # for image
            for pic in pics:
                img_name=''
                if '?KID=' in pic:
                    img_name = re.compile(
                        '.*?KID=').findall(pic.split('/')[-1])[0][:-5]
                else:
                    img_name = pic.split('/')[-1]
                url_names.append((pic,img_name))
        return url_names
comment=Comment()

user=User()

follow=Follow()
hot=Hot()

mblog=Mblog()
video=Video()
img=Img()

if __name__=="__main__":
    c=Comment()
    print(c.extract_img(c.get({'mid':"4694521848529087"})))
    f=Follow()
    total,users=f.get(5716616140)
    print(total,users)
    h=Hot()
    print(h.get())
    m=Mblog()
    print(m.extract_mblogs(5716616140))

    v=Video()
    ss={'_id': '4669445920785354', 'alchemy_params': {'ug_red_envelope': False}, 'attitudes_count': 2993, 'bid': 'Kt8By3ij0', 'can_edit': False, 'comments_count': 1090, 'content_auth': 0, 'created_at': 'Thu Aug 12 19:02:04 +0800 2021', 'darwin_tags': [], 'edit_config': {'edited': False}, 'enable_comment_guide': True, 'extern_safe': 0, 'favorited': False, 'fid': 4669365235744804, 'hide_flag': 0, 'id': '4669445920785354', 'isLongText': False, 'is_paid': False, 'mblog_menu_new_style': 0, 'mblog_vip_type': 0, 'mblogtype': 0, 'mid': '4669445920785354', 'mlevel': 0, 'more_info_type': 0, 'page_info': {'type': 'video', 'object_type': 11, 'url_ori': 'http://t.cn/A6If5bxO', 'page_pic': {'width': 3840, 'pid': '006EPFJBly1gtdypkv05yj31hc0u0qdv', 'source': 1, 'is_self_cover': 1, 'type': 1, 'url': 'https://wx1.sinaimg.cn/crop.0.6.1920.1067/006EPFJBly1gtdypkv05yj31hc0u0qdv.jpg', 'height': 2134}, 'page_url': 'https://video.weibo.com/show?fid=1034%3A4669364654506010&luicode=10000011&lfid=1076036100165591', 'object_id': '1034:4669364654506010', 'page_title': '刘老师说电影的微博视频', 'title': '人类内斗起来，就没丧尸什么事了！', 'content1': '刘老师说电影的微博视频', 'content2': '女王行为！卡妈归来战斗力 爆表！刘老师爆笑解说《行尸走肉》第五季#金牌解说#', 'video_orientation': 'horizontal', 'play_count': '55万次播放', 'media_info': {'stream_url': 'https://f.video.weibocdn.com/adxR1qiDlx07OY1AlMju01041201zEhu0E010.mp4?label=mp4_ld&template=640x360.25.0&trans_finger=6006a648d0db83b7d9951b3cee381a9c&ori=0&ps=1CwnkDw1GXwCQx&Expires=1628797484&ssig=512JDqskaZ&KID=unistore,video', 'stream_url_hd': 'https://f.video.weibocdn.com/sgZneB4ulx07OY1ARW4U01041202rTvG0E010.mp4?label=mp4_hd&template=852x480.25.0&trans_finger=d8257cc71422c9ad30fe69ce9523c87b&ori=0&ps=1CwnkDw1GXwCQx&Expires=1628797484&ssig=9qUZDCePCC&KID=unistore,video', 'duration': 660.096}, 'urls': {'mp4_720p_mp4': 'https://f.video.weibocdn.com/StjmUUb5lx07OY1BLztC01041204KTK50E020.mp4?label=mp4_720p&template=1280x720.25.0&trans_finger=775cb0ab963a74099cf9f840cd1987f1&ori=0&ps=1CwnkDw1GXwCQx&Expires=1628797484&ssig=CYaUkAPYYH&KID=unistore,video', 'mp4_hd_mp4': 'https://f.video.weibocdn.com/sgZneB4ulx07OY1ARW4U01041202rTvG0E010.mp4?label=mp4_hd&template=852x480.25.0&trans_finger=d8257cc71422c9ad30fe69ce9523c87b&ori=0&ps=1CwnkDw1GXwCQx&Expires=1628797484&ssig=9qUZDCePCC&KID=unistore,video', 'mp4_ld_mp4': 'https://f.video.weibocdn.com/adxR1qiDlx07OY1AlMju01041201zEhu0E010.mp4?label=mp4_ld&template=640x360.25.0&trans_finger=6006a648d0db83b7d9951b3cee381a9c&ori=0&ps=1CwnkDw1GXwCQx&Expires=1628797484&ssig=512JDqskaZ&KID=unistore,video'}}, 'pending_approval_count': 0, 'pic_ids': [], 'pic_num': 0, 'pic_types': '', 'reposts_count': 875, 'reward_exhibition_type': 0, 'rid': '1_0_50_4813850309442391440_0_0_0', 'show_additional_indication': 0, 'source': '微博视频号', 'spider_time': 1628793955.97164, 'text': '女王行为！卡妈归来战斗力爆表！刘老师 爆笑解说《行尸走肉》第五季<a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E9%87%91%E7%89%8C%E8%A7%A3%E8%AF%B4%23&luicode=10000011&lfid=1076036100165591" data-hide=""><span class="surl-text">#金牌解说#</span></a> <a data-url="http://t.cn/A6If5bxO" href="https://video.weibo.com/show?fid=1034:4669364654506010" data-hide=""><span class=\'url-icon\'><img style=\'width: 1rem;height: 1rem\' src=\'https://h5.sinaimg.cn/upload/2015/09/25/3/timeline_card_small_video_default.png\'></span><span class="surl-text">刘老师说电影的微博视频</span></a> ', 'textLength': 93, 'uid': 6100165591, 'user': {'id': 6100165591, 'screen_name': '刘老师说电影', 'profile_image_url': 'https://tvax2.sinaimg.cn/crop.0.0.1080.1080.180/006EPFJBly8gditlvnl62j30u00u0tae.jpg?KID=imgbed,tva&Expires=1628804684&ssig=sb6oTG9jY1', 'profile_url': 'https://m.weibo.cn/u/6100165591?uid=6100165591&luicode=10000011&lfid=1076036100165591', 'statuses_count': 976, 'verified': True, 'verified_type': 0, 'verified_type_ext': 1, 'verified_reason': '微博2019十大影响力电影视频博主 电影视频自媒体', 'close_blue_v': False, 'description': '微博2018十大影响力电影大V 电影视频自媒体', 'gender': 'm', 'mbtype': 12, 'urank': 32, 'mbrank': 7, 'follow_me': False, 'following': False, 'followers_count': 5177562, 'follow_count': 275, 'cover_image_phone': 'https://wx1.sinaimg.cn/crop.0.0.640.640.640/006EPFJBly1flojft1118j30yi0yhmyw.jpg', 'avatar_hd': 'https://wx2.sinaimg.cn/orj480/006EPFJBly8gditlvnl62j30u00u0tae.jpg', 'like': False, 'like_me': False, 'badge': {'bind_taobao': 1, 'follow_whitelist_video': 1, 'video_attention': 4, 'user_name_certificate': 1, 'wenchuan_10th': 1, 'super_star_2018': 1, 'weibo_display_fans': 1, 'relation_display': 1, 'v_influence_2018': 1, 'hongbaofei_2019': 1, 'hongrenjie_2019': 1, 'rrgyj_2019': 1, 'weishi_2019': 1, 'gongjiri_2019': 1, 'hongbao_2020': 2, 'pc_new': 6, 'hongrenjie_2020': 1, 'nihaoshenghuojie_2021': 1}}, 'version': 2, 'visible': {'type': 0, 'list_id': 0}}
    print(v.extract(ss) )   