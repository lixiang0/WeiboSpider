import threading
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
import os,logging,time
from youran.disks import Min
min = Min()

# main = logging.getLogger('main')
# main.setLevel(logging.DEBUG)
main=youran.logger

def thread_all(name):
    while True:
        try:
            ids = set()
            for id in db.follow.random(20000):
                if 'blogger' in id:
                    ids.add(id['blogger'])
            if len(ids)==0:
                ids = set([1865990891])
            for uid in ids:
                #   duplicate=False for download bug ,if True ,download once only
                code,msg=utils.getall(uid=uid,duplicate=False,cookie=False,proxy=True)
                youran.logger.warning(f'code={code},msg={msg}')
                utils.sleep(20,1*60)
        except Exception as e:
            youran.logger.error('遇到异常，错误为：'+repr(e))
            utils.sleep(10*60,40*60)



def thread_follow(name):
    while True:
        try:
            seeds=set()
            comments=youran.db.comment.random(2000)
            for _comment in comments:
                if 'data' in _comment:
                    if 'data' in _comment['data']:
                        for item in _comment['data']['data']:
                            seeds.add(item['user']['id'])
                    else:
                        continue
            if len(seeds)==0:
                seeds=set([6390144374])
            while len(seeds) != 0:
                uid = seeds.pop()
                current_page = 1
                while True:
                    main.warning(f'{uid}')
                    total, users = youran.net.follow.get(uid, current_page,proxy=True)
                    if users is None:
                        print('本用户抓取结束')
                        break
                    for user in users:
                        main.warning(repr(user['_id'])+"   "+user['screen_name'])
                        user=utils.update_avatar(user)
                        assert youran.db.user.add(user)  is True
                        assert youran.db.follow.add({'_id': str(uid)+str(user['id']), 'fans': int(uid), 'blogger': int(user['id'])}) is True
                    current_page += 1
                utils.sleep(10,50)
        except Exception as e:
            youran.logger.error('遇到异常，错误为：'+repr(e))
            utils.sleep(10*60,40*60)
def thread_hot(name):
    while True:
        try:
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
                            utils.download_mblog({'bid':bid,'isLongText':True},'uid','current_page','total_page',duplicate=False,proxy=True)
                            utils.sleep(5, 10)
            utils.sleep(10*60,30*60)
        except Exception as e:
            youran.logger.error('遇到异常，错误为：'+repr(e))
            utils.sleep(10*60,40*60)


def thread_my(name):
    while True:
        try:
            ids=[]
            users =[user for user in  youran.db.account.random()]
            for user in users:
                youran.logger.warning(user)
                ids+=youran.db.follow.find_follows(id=user['_id'])#set(config.IDS)6390144374
            youran.logger.warning(ids)
            # ids=db.follow.find_follows(id=6390144374)
            i = 0
            for uid in ids:
                uid=int(uid['blogger'])
                youran.logger.warning(f'当前爬取的用户ID为：{uid}')
                username=list(youran.db.user.find({'_id':uid}))[0]['screen_name']
                youran.logger.warning(f'当前爬取的用户为：{username}')
                youran.logger.warning('*'*100)
                code,msg=utils.getall(uid=uid,duplicate=True,cookie=True,proxy=False,one_page=True)
                youran.logger.warning(f'code={code},msg={msg}')
                utils.sleep(20,1*60) 
                youran.logger.warning(f'本id:{username}抓取结束..')
            utils.sleep(20*30, 30*60)
        except Exception as e:
            youran.logger.error('遇到异常，错误为：'+repr(e))
            utils.sleep(10*60,40*60)
def thread_state(name):
    while True:
        IS_NEW_DAY,year,month,day,hour=youran.utils.isnewday()
        # if IS_NEW_DAY:
        count=youran.utils.db.mblog.counts()
        authors=youran.utils.db.user.counts()
        youran.db.states.add({'_id':f'user_count_{year}{month}{day}','name':'user_count','update_time':f'{year}{month}{day}','count':authors})
        youran.db.states.add({'_id':f'mblog_count_{year}{month}{day}','name':'mblog_count','update_time':f'{year}{month}{day}','count':count})
        youran.logger.warning(f'每日更新完成，时间：{year}:{month}:{day}')
        youran.utils.sleep(23*60*60,24*60*60)

if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    logging.info("Main    : before creating thread")
    # x = threading.Thread(target=thread_follow, args=(1,))
    # y = threading.Thread(target=thread_all, args=(1,))
    z = threading.Thread(target=thread_hot, args=(1,))
    # z1 = threading.Thread(target=thread_my, args=(1,))
    z2 = threading.Thread(target=thread_state, args=(1,))
    threads=[z,z2]
    logging.info("Main    : before running thread")
    [_.start() for _ in threads]
    logging.info("Main    : wait for the thread to finish")
    [_.join() for _ in threads]
    logging.info("Main    : all done")