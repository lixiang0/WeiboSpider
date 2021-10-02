# -*- coding: utf-8 -*-
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
import os,logging,time



main = logging.getLogger('main')
main.setLevel(logging.DEBUG)


while True:
    scount=dict()
    seeds=[]
    mblogs=youran.db.mblog.random(20)
    for mblog in mblogs:
        if 'mblog' in mblog:
            seeds.append(mblog['user']['id'])
    while len(seeds) != 0:
        uid = seeds.pop()
        if uid in scount:
            scount[uid]+=1
            if scount[uid]>10:
                continue
        else:
            scount[uid]=0
        current_page = 1
        while True:
            total, users = youran.net.follow.get(uid, current_page)
            if users is None:
                scount[uid]+=1
                main.warning('本用户抓取结束')
                break
            for user in users:
                main.warning(user['screen_name'])
                # main.warning(user['screen_name'])
                youran.db.user.add_user(user)
                youran.db.follow.add({'_id': str(uid)+str(user['id']), 'fans': int(uid), 'blogger': int(user['id'])})
                youran.db.states.add({'name':'all_follow','update_time':time.asctime( time.localtime(time.time()) )})
            current_page += 1
    else:
        seeds = youran.db.follow.all_bloggers()-youran.db.follow.all_follows()
        if len(seeds) == 0:
            break
