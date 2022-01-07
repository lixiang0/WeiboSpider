'''http://www.xiladaili.com/https/
http://www.xiladaili.com/https/1/
http://www.xiladaili.com/https/2/
http://www.xiladaili.com/https/3/'''

import requests
from scrapy.selector import Selector
from . import headers
import time,pymongo

# writer=open('ips2.txt','w+')
#http  2000
#https 2000
#gaoni 2000
import youran
# db_proxies = youran.db_proxy['db_proxy']

# def add(proxy):
#     try:
#         db_proxies.update({'_id': proxy['_id']}, {
#             '$set': proxy}, upsert=True)
#         return True
#     except pymongo.errors.DuplicateKeyError:
#         return False
def xila():
    for t in ['https','gaoni','http']:
        for i in range(2000)[1:]:
            url=f'http://www.xiladaili.com/{t}/{i}/' if i>1 else f'http://www.xiladaili.com/{t}'
            print(url)
            res=requests.get(url,headers=headers.pc)
            # print(res.text)
            trs=Selector(text=res.text).xpath('//tr').getall()[1:]
            # print(tr)
            if len(trs) == 0:
                print('page is out of range....')
                break
            for tr in trs:
                tds=Selector(text=tr).xpath('//td/text()').getall()
                print(tds)
                # 免费ip代理	IP匿名度	IP类型	IP位置	响应速度	存活时间	最后验证时间	打分
                ip=tds[0]
                niming=tds[1]
                leixing=tds[2]
                location=tds[3]
                ping=tds[4]
                alive=tds[5]
                validate_time=tds[6]
                score=tds[7]
                youran.db.proxy.add({'_id':ip,'ip':ip,'niming':niming,'leixing':leixing,'location':location,'ping':ping,'alive':alive,'validate_time':validate_time,'score':score})
            time.sleep(45)