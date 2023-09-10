import json
from . import headers
from . import db
import requests,tqdm,io,re
from scrapy.selector import Selector
import urllib
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
def allowed_gai_family():
    family = socket.AF_INET # force IPv4
    return family
urllib3_cn.allowed_gai_family = allowed_gai_family
class BaseNet():
    @staticmethod
    def baseget(url,cookie=False,header='pc',proxy=True):
        # print(url)
        cookies=headers.cookies if cookie else None
        # tunnel = random.randint(1,10000)
        headers1 =headers.pc if header == 'pc' else headers.mobile
        # headers1["Proxy-Tunnel"]=str(tunnel)
        _proxies=db.proxy.get_randomip() if proxy else None
        r=requests.get(url, headers=headers1,cookies=cookies,verify=False,proxies=_proxies,timeout=30)
        # r.encoding = r.apparent_encoding
        return r.text

    @staticmethod
    def download(url,progress=False,headers=headers.mobile):
        response=requests.get(url, headers=headers, stream=True,timeout=30,verify=False,proxies=db.proxy.get_randomip())
        if response.status_code!=200:
            return None
        if 'Content-length' not in response.headers:
            return None
        file_size=response.headers['Content-length']
        pbar=None
        if progress:
            pbar=tqdm.tqdm(total=int(file_size),unit='B',unit_scale=True,desc=url.split('/')[-1][:20])
        with io.BytesIO() as f:
            for chunk in response.iter_content(chunk_size=1024):
                if  chunk:
                    f.write(chunk)
                    if progress:
                        pbar.update(1024)
            if progress:
                pbar.close()
            return f.getvalue()

class Comment(BaseNet):
    
    def get(self,mblog,maxid=None,cookie=True,proxy=False):
        mid=mblog['mid']
        comment_url=f'https://m.weibo.cn/comments/hotflow?id={mid}&mid={mid}'
        comment_url=comment_url+f'&max_id={maxid}' if maxid else comment_url
        try:
            res = self.baseget(comment_url,cookie=cookie,proxy=proxy)
            # print(res)
            if '微博-出错了' in res:
                return None
            comments=json.loads(res)
            comments['mid']=mid
            comments['_id']=mid
            return comments
        except Exception as e:
            print(repr(e))
            return None #网络错误


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
    def get(self,uid, page=1,proxy=False):
        follows_url = f'https://m.weibo.cn/api/container/getIndex?containerid=231051_-_followers_-_{uid}_-_1042015:tagCategory_019'
        next_url = follows_url+f'&page={page}' if page > 1 else follows_url
        res = self.baseget(next_url)
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
        detail_response=self.baseget(url,header='pc1',cookie=True)
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
    def extract_mblogs1(self,uid, page=1,cookie=False,proxy=False):
        # page_url=f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}&feature=0'
        # 1663072851
        next_url=f'https://m.weibo.cn/api/container/getIndex?containerid=230413{uid}_-_WEIBO_SECOND_PROFILE_WEIBO&page_type=03&page={page}'
        # next_url = f'https://weibo.com/ajax/statuses/mymblog?uid={uid}&page={page}'
        obj=None
        try:
            print('next_url:',next_url)
            res = self.baseget(next_url,cookie=cookie,proxy=proxy)
            # print(res)
            if '100005' in res:
                return -2,'请求过于频繁' #请求过于频繁
            obj=json.loads(res)
        except Exception as e:
            return -3,repr(e) #网络错误
        mblogs = []
        if obj['ok'] == 1:
            for card in obj['data']['cards']:
                if card['card_type']==9:
                    mblogs.append(card['mblog']) 
        else:
            return -1,obj #可能需要重新登录
        return 0, mblogs
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
        url=f'https://m.weibo.cn/api/container/getIndex?uid={id}&t=0&luicode=10000011&lfid=100103type%3D3%26q%3D3164402322%26t%3D0&containerid=1005053164402322'
        # url=f'https://m.weibo.cn/profile/info?uid={id}'
        # print(url)
        res = self.baseget(url,header='')
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
    def extract(self,mblog):
        # 解析视频地址video:mblog['mblog']['page_info']['media_info']['stream_url']
        # 字段的示例参考10.×.py文件
        if not mblog:
            return None,None
        object_id = ''
        if 'page_info' in mblog.keys():
            if mblog['page_info']['type'] == 'video':
                object_id = mblog['page_info']['object_id']
                # for video
                if len(object_id) > 2:
                    # f'https://m.weibo.cn/status/{bid}?fid={object_id}'
                    if 'media_info' not in mblog['page_info'].keys():
                        return
                    video_url = mblog['page_info']['media_info']['stream_url']
                    video_name = ''
                    if video_url is not ' ' and video_url is not '':
                        # http://flv.bn.netease.com/videolib3/1602/25/DCmck9663/HD/DCmck9663-mobile.mp4
                        if 'cntv.vod.cdn.myqcloud.com' in video_url or 'flv.bn.netease.com' in video_url:
                            video_name = video_url.split('/')[-1]
                        # http://miaopai.video.weibocdn.com/y8uhGmpklx07hgllSbT20104020118Td0E013?Expires=1580820449&ssig=Tyclwn1zHP&KID=unistore,video
                        # http://miaopai.video.weibocdn.com/004isPQTlx07w78L1b5S010412010UgY0E013.mp4?label=mp4_hd&template=852x480.24.0&trans_finger=ac6fb6d5c49a67fe2901ae638b222ab2&Expires=1580806190&ssig=YrHlNViWdZ&KID=unistore,video
                        elif 'miaopai.video.weibocdn.com' in video_url:
                            if '?Expires=' in video_url:
                                video_name = re.compile(
                                    '.*?Expires').findall(video_url)[0].split('/')[-1][:-8]+'.mp4'
                            if '.mp4?label=mp4_hd' in video_url:
                                video_name = re.compile(
                                    '.*.mp4\?').findall(video_url)[0][:-1].split('/')[-1]
                        # http://api.ivideo.sina.com.cn/public/video/play/url?appname=weibocard&appver=0.1&applt=web&tags=weibocard&direct=1&vid=32183307201
                        elif 'api.ivideo.sina.com.cn' in video_url:  # 需要redirect
                            video_url = urllib.request.urlopen(
                                video_url).geturl()  # redirect之后再解析
                            mblog['page_info']['media_info']['stream_url'] = video_url
                            res = re.findall('n/(.*).(mp4|m3u8)\?', video_url)[0]
                            video_name = res[0]+'.'+res[1]
                        # https://us.sinaimg.cn/0048hC0kjx06YLljHDni010d0100006H0k01.m3u8?KID=unistore,video&Expires=1582024223&ssig=Kbnro7UusO&KID=unistore,video
                        # https://us.sinaimg.cn/0023jkOujx07bacCMKDK010f1100fYwu0k01.mp4?label=mp4_hd&Expires=1582079291&ssig=4wjkt3+R4g&KID=unistore,video,开始下载
                        elif 'https://us.sinaimg.cn' in video_url:
                            video_name = re.findall('n/(.*).(mp4|m3u8)\?',video_url)
                            video_name=video_name[0][0]+'.'+video_name[0][1]
                        # https://api.youku.com/videos/player/file?data=WcEl1oUuTdTROalV5T0RFd09BPT18MHwxfDEwMDUw
                        elif 'https://api.youku.com' in video_url:
                            video_name = video_url.split('data=')[1]+'.mp4'
                        # http://edge.ivideo.sina.com.cn/96148152.mp4?KID=sina,viask&Expires=1582214400&ssig=TafyOUtj%2Ff
                        elif 'edge.ivideo.sina.com.cn' in video_url:
                            video_name = re.findall(
                                '/(.*).mp4', video_url)[0]+'.mp4'
                        # http://mvvideo2.meitudata.com/581e9c3a91f903898.mp4
                        elif 'http://mvvideo2.meitudata.com' in video_url:#/581e9c3a91f903898.mp4
                            video_name=re.findall('m/(.*).(mp4|m3u8)',video_url)[0]
                            video_name=video_name[0]+'.'+video_name[1]
                        else:
                            video_name = re.compile(
                                r'.*.mp4\?').findall(video_url.split('/')[-1])
                            if len(video_name) > 0:
                                video_name = video_name[0][:-1]
                            else:
                                video_name = 'None.mp4'
                        return video_url,video_name
        return None,None
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