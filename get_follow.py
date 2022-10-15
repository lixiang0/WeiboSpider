
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
import os,logging,time



main = logging.getLogger('main')
main.setLevel(logging.DEBUG)
# youran.db.db_client = pymongo.MongoClient(f"mongodb://{os.environ['DBIP']}:{os.environ['DBPort']}/")["db_weibo1"]
# print(os.environ['DBIP'])
while True:
    scount=dict()
    seeds=set()
    # mblogs=youran.db.follow.random(20)
    # for mblog in mblogs:
    #     # if 'mblog' in mblog:
    #         # seeds.append(mblog['user']['id'])
    #     seeds.add(repr(mblog['blogger']))
    if len(seeds)==0:
        seeds=set([6390144374])    
    while len(seeds) != 0:
        uid = seeds.pop()
        if uid in scount:
            scount[uid]+=1
            if scount[uid]>10:
                continue
        else:
            scount[uid]=0
        # main.warning(f'{uid},failed num:{scount[uid]}***********************************')
        current_page = 1
        while True:
            main.warning(f'{uid}')
            total, users = youran.net.follow.get(uid, current_page,proxy=True)
            if users is None:
                scount[uid]+=1
                print('本用户抓取结束')
                break
            # page_num = total/20 if total % 20 == 0 else total/20+1
            # print(current_page, total, users)
            for user in users:
                # print(user['screen_name'])
                main.warning(repr(user['_id'])+"   "+user['screen_name'])
                assert youran.db.user.add(user)  is True
                assert youran.db.follow.add({'_id': str(uid)+str(user['id']), 'fans': int(uid), 'blogger': int(user['id'])}) is True
                assert youran.db.states.add({'name':'所有用户：','update_time':time.asctime( time.localtime(time.time()) )}) is True
            current_page += 1
        # utils.sleep(10,50)
    # else:
    #     seeds = youran.db.follow.bloggers()#-youran.db.Follow().all_follows()
    #     if len(seeds) == 0:
    #         break
