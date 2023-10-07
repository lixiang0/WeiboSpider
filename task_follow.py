
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
import os,logging,time,math
while True:
    seeds=set()
    TAG=False
    if TAG:
        mblogs=youran.db.follow.find({})#random(20)
        for mblog in mblogs:
            seeds.add(repr(mblog['blogger']))
    else:
        comments=youran.db.comment.random(200)
        for _comment in comments:
            if 'data' in _comment:
                if 'data' in _comment['data']:
                    for item in _comment['data']['data']:
                        seeds.add(item['user']['id'])
                else:
                    continue
    if len(seeds)==0:
        seeds=set([7360938000]) 
    LENGTH=len(seeds)   
    while len(seeds) != 0:
        uid = seeds.pop()
        current_page = 0
        total_page=0
        while True:
            if current_page>10:#微博只让抓前10页
                youran.logger.warning('本用户抓取结束,已抓取全部页面.....')
                break
            youran.logger.warning(f'当前id：{uid}，已爬取{LENGTH-len(seeds)}，还剩{len(seeds)}/{LENGTH}')
            youran.logger.warning(f'{uid}')
            users=None
            total=None
            try:
                total, users = youran.net.follow.get(uid, current_page,proxy=True,cookie=False)
            except Exception as e:
                youran.logger.warning(f'遇到网络问题：{repr(e)}')
                continue
            if users is None or total is None:
                youran.logger.warning('本用户抓取结束,原因：返回为空')#11页之后为空
                break
            total_page = math.ceil(total/20)
            youran.logger.warning(f'本用户总关注{total}个博主,当前第{current_page}页，总{total_page}页......')
            for user in users:
                if youran.db.user.counts({'_id':user['_id']})>0:
                    youran.logger.warning(f'{current_page}/{total_page}--------'+repr(user['_id'])+"   "+user['screen_name']+"已存在，跳过")
                    continue
                youran.logger.warning(f'{current_page}/{total_page}--------'+repr(user['_id'])+"   "+user['screen_name'])
                youran.logger.warning('开始更新头像')
                try:
                    utils.update_avatar(user)
                    youran.logger.warning('更新头像成功')
                except Exception as e:
                    youran.logger.warning(f'出现网络错误...{repr(e)}\n头像未更新，本次只更新用户信息.......')
                    utils.sleep(10,1*60)
                assert youran.db.user.add(user)  is True
                assert youran.db.follow.add({'_id': str(uid)+str(user['id']), 'fans': int(uid), 'blogger': int(user['id'])}) is True
            utils.sleep(1,5)
            current_page += 1
        utils.sleep(10,50)
        # break
    # break