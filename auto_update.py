import pymongo
import datetime
import time
import requests
import random
import json
import re
from scrapy.selector import Selector
import os
import urllib
import logging
import config
# automatically fetch mblog for every 30m in 6:00-23:00

# demo :爱可可-爱生活 1402400261
id_names = {
    '1402400261': '爱可可-爱生活',
}

# 1.time define
start_hour = 6
end_hour = 23
now_hour = datetime.datetime.now().hour

# 2.init datebase
myclient = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
mydb = myclient["db_weibo"]
db_mblogs = mydb['db_mblogs']
db_links = mydb['db_links']

if now_hour > start_hour and now_hour < end_hour:
# if True:
    log_name=time.ctime(time.time()).replace(' ', '_')
    logging.basicConfig(filename=f'logs/{log_name}.log', filemode='w+',
                    format='%(levelname)s - %(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    logging.warning('start fetching lastest mblogs...')
    for id in id_names.keys():
        mblogs_url = f'https://m.weibo.cn/api/container/getIndex?uid={id}&lfid=2304136390144374_-_WEIBO_SECOND_PROFILE_WEIBO&containerid=107603{id}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
                   }
        current_page = 1
        next_url = mblogs_url+f'&page={current_page}'
        err_count = 0
        while True:
            logging.warning(id_names[id]+f'----current url:{next_url}')
            response = requests.get(next_url, headers=headers)
            obj = json.loads(response.text)
            duplicated = False
            if obj['ok'] == 1:
                try:
                    db_links.insert_one(  # 保存每次爬取的json字符串
                        {
                            '_id': time.time(),
                            'text': response.text
                        })
                except pymongo.errors.DuplicateKeyError:
                    continue
                cards = obj['data']['cards']
                for card in cards:
                    if 'mblog' not in card:  # 处理mblog不存在的情况
                        continue
                    logging.warning(id_names[id]+f'----处理card content:{str(card)}')
                    mblog = card['mblog']
                    mid = mblog['id']
                    created_at = mblog['created_at']
                    text = mblog['text']
                    source = mblog['source']
                    reposts_count = mblog['reposts_count']
                    comments_count = mblog['comments_count']
                    attitudes_count = mblog['attitudes_count']
                    mblogtype = mblog['mblogtype']
                    pic_num = mblog['pic_num']
                    isLongText = mblog['isLongText']
                    bid = mblog['bid']
                    retweeted_id = mblog['retweeted_status']['mid'] if 'retweeted_status' in mblog.keys(
                    ) else 0  # 这里记住需要抓取被转发的微博
                    pics = []
                    # 解析视频地址video:mblog['mblog']['page_info']['media_info']['stream_url']
                    # 字段的示例参考10.×.py文件
                    object_id = ''
                    if 'page_info' in mblog.keys():
                        if mblog['page_info']['type'] == 'video':
                            object_id = mblog['page_info']['object_id']
                    if not isLongText:
                        if 'pics' in mblog.keys():
                            pics = [pic['large']['url']
                                    for pic in mblog['pics']]
                    else:
                        # 对于长微博需要跳转具体微博，才能查看全部内容
                        # https://m.weibo.cn/detail/{mid}
                        long_text_url = 'https://m.weibo.cn/detail/'+mid
                        logging.warning('长微博：'+long_text_url)
                        long_text_response = requests.get(
                            long_text_url, headers=headers).text
                        res = re.compile(
                            r'var\ \$render_data = \[\{.*\}\]\[0\]\ \|\|\ \{\};', re.DOTALL).findall(long_text_response)
                        if len(res) < 1:
                            break
                        res = res[0].replace('\n', '')[20:-11]
                        if json.loads(res)['status']['ok'] == 1:
                            mtext = json.loads(res)['status']
                            text = mtext['text']
                            if 'pics' in mtext.keys():
                                pics = [pic['url']
                                        for pic in json.loads(res)['status']['pics']]
                    try:
                        blog={
                                '_id': mid,
                                'retweeted_id': retweeted_id,  # mid
                                'bid': bid,
                                'uid': id,
                                'created_at': created_at,
                                'text': text,
                                'source': source,
                                'reposts_count': reposts_count,
                                'comments_count': comments_count,
                                'attitudes_count': attitudes_count,
                                'spider_time': str(time.time()),
                                'imgs': '\t'.join(pics),
                                # for video,https://m.weibo.cn/status/{bid}?fid={object_id}
                                'object_id': object_id,
                            }
                        db_mblogs.insert_one(blog)
                        logging.warning(id_names[id]+f'----解析出微博:{str(blog)}')
                    except pymongo.errors.DuplicateKeyError:
                        err_count += 1
                        if err_count > 5:
                            logging.error(id_names[id]+f'----当前页重复的微博:{str(err_count)}条，停止更新')
                            duplicated = True
                            break
                if duplicated:
                    break
                current_page += 1
                next_url = mblogs_url + \
                    f'&page={str(current_page)}'  # 4400073968382627
                sleep_time = random.randint(6, 15)
                time.sleep(sleep_time)
            else:
                break

    # for image:
    logging.warning('开始下载图片...')
    db_imgs = mydb['db_imgs']
    imgs = db_mblogs.find({}, {'imgs': 1})
    imgs = [img['imgs'].split('\t') for img in imgs if len(img['imgs']) > 2]
    logging.warning(f'image count:{len(imgs)}')
    import glob
    files = [img for img in glob.glob(
        config.ROOT+'imgs/*') if os.path.getsize(img) > 0]  # 剔除文件大小为0
    length = len(imgs)
    for li in imgs:
        length -= 1
        logging.warning(str(length))
        for img in li:
            name = img.split('/')[-1]
            if config.ROOT+'imgs/'+name in files:
                continue
            logging.warning(img)
            response = requests.get(img, headers=headers, stream=True)
            if response.status_code == 200:
                with open(config.ROOT+"imgs/"+name, 'wb') as f:
                    f.write(response.content)
                db_imgs.insert_one({'url': img, 'file_name': name})
            time.sleep(1)
    # for video
    logging.warning('开始下载视频...')
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
               'Sec-Fetch-Mode': 'same-origin',
               'Upgrade-Insecure-Requests': '1',
               }
    db_videos = mydb['db_videos']
    results = db_mblogs.find({}, {'object_id': 1, 'bid': 1, '_id': 0})
    spider_videos = db_videos.find({}, {'object_id': 1, '_id': 0})
    object_ids = [(video['object_id'], video['bid'])
                  for video in results if 'object_id' in video.keys() and len(video['object_id']) > 2]
    spider_videos = [video['object_id'] for video in spider_videos if 'object_id' in video.keys(
    ) and len(video['object_id']) > 2]
    logging.warning(f'videos url count:{len(object_ids)}', object_ids[:2])

    files = [video for video in glob.glob(
        config.ROOT+'videos/*') if os.path.getsize(video) > 0]  # 剔除文件大小为0
    logging.warning(f'videos file count:{len(files)}', files[:2])

    for (oid, bid) in object_ids:
        if oid in spider_videos:
            # print('pass')
            continue
        video_url = f'https://m.weibo.cn/status/{bid}?fid={oid}'
        video_url_response = requests.get(video_url, headers=headers)
        if video_url_response.status_code == 200:
            video_url_response = video_url_response.text
            res = re.compile(
                r'var\ \$render_data = \[\{.*\}\]\[0\]\ \|\|\ \{\};', re.DOTALL).findall(video_url_response)
            res = res[0].replace('\n', '')[20:-11]
            url = ''
            video_name = ''
            # print(res)
            if json.loads(res)['status']['ok'] == 1:
                logging.warning(url)
                url = json.loads(
                    res)['status']['page_info']['media_info']['stream_url_hd']
                if url == '':  # 有可能出现的链接过期的情况。
                    continue
                if '.mp4?' not in url:  # 需要redirect
                    url = urllib.request.urlopen(url).geturl()# redirect之后再解析
            else:
                continue
            if '.mp4' not in url:
                continue
            if 'https://cntv.vod.cdn.myqcloud.com' in url:
                video_name = url.split('/')[-1]
            elif 'miaopai.video.weibocdn.com' in url:
                video_name = re.compile('/.*?').findall(url)[0][-2:-1]+'.mp4'
            else:
                video_name = re.compile(
                    r'.*.mp4\?').findall(url.split('/')[-1])[0][:-1]
            if config.ROOT+'videos/'+video_name in files:
                logging.warning('local file exists...'+video_name)
                continue
            try:
                response = requests.get(url, headers=headers, stream=True)
                if response.status_code == 200:
                    with open(config.ROOT+'videos/'+video_name, 'wb') as f:
                        f.write(response.content)
                    db_videos.insert_one(
                        {'object_id': oid, 'video_name': video_name})
                    print('download successfully:', video_name)
                else:
                    print(f'error:{url},{video_name},{response.status_code}')
            except Exception as e:
                print(f'error:{video_name}')

else:
    print('time to sleep,quit....')
