# coding=utf-8
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *

import logging
import datetime
import time
import math
from youran.disks import Min
import json

main = logging.getLogger('main')
main.setLevel(logging.DEBUG)
min = Min()

def getall(uid,duplicate=False,cookie=False,proxy=True):
    uid=int(uid)
    username=youran.db.user.find_users([uid])[0]['screen_name']
    main.warning(f'当前爬取的用户ID为：uid={uid},username={username}')
    main.warning('*'*100)
    total_mblogs ,msg = youran.net.mblog.extract_mblogs(uid, 0,cookie=cookie,proxy=proxy)
    if total_mblogs<0:
        main.warning('当前请求失败，错误原因：'+msg)
        main.warning('停止抓取,休息一会儿再爬取。。。。。。')
        return -1,msg

    total_page = math.ceil(total_mblogs/10)
    main.warning(f'当前计算得到总页数:{int(total_page)},总博文数目:{int(total_mblogs)}')
    current_page =100 if total_page>100 else total_page#total_page+1  #这里加1是因为while循环总是先减一
    while True:
        if current_page<2:# 原因：total_page+1--> 1+1
            break
        current_page -= 1
        _page=total_page+1-current_page  #存储到数据库中，最后一页编号为1。这里与微博相反。
        obj={'_id':str(uid)+str(_page),'uid':uid,'page':_page}
        if youran.db.log.find(obj) and not duplicate:#存在 且不重复
            main.warning(f'({uid}:{current_page}/{total_page})------当前用户{username}第{current_page}已经爬取过且duplicate={duplicate}，跳过.........')
            continue
        main.warning(f'({uid}:{current_page}/{total_page})------当前用户为{username},爬取页数为：current_page={current_page}')
        main.warning(f'({uid}:{current_page}/{total_page})------开始抽取本页中的博文：')
        TAG, mblogs = youran.net.mblog.extract_mblogs(uid, current_page,cookie=cookie,proxy=proxy)
        if not mblogs or TAG<0:  # 抓取太频繁   
            main.warning(f'({uid}:{current_page}/{total_page})------抓取到了末尾，停止抓取。。。。。。TAG={TAG},info={mblogs}')
            return -1,mblogs
        main.warning(f'({uid}:{current_page}/{total_page})------解析成功.........')
        main.warning(f'({uid}:{current_page}/{total_page})------开始解析本页博文.........')
        main.warning('*'*100)
        for mblog in mblogs:
            #Tue Sep 28 20:12:48 2021
            timeint=time.mktime(datetime.datetime.strptime(mblog['created_at'],
                                                    "%a %b %d %H:%M:%S %z %Y").timetuple())
            mblog['created_at1']=timeint
            utils.download_mblog(mblog,uid,current_page,total_page,duplicate=False,cookie=cookie,proxy=proxy)
        youran.db.log.add({'_id':str(uid)+str(_page),'uid':uid,'page':_page})
        utils.sleep(5, 10)
    main.warning(f'本id:{uid}，用户名：{username}抓取结束..')
    main.warning(f'总共{total_page}页微博,实际抓取到{total_page-current_page+1}页微博')      
    youran.db.states.add({'name':'更新所有微博：','update_time':time.asctime( time.localtime(time.time()) )})
    return 0,'success'

