import requests
from scrapy.selector import Selector
import time,pymongo
import sys,os
from pprint import pprint
#获取根目录路径
src_dir = os.path.dirname(os.path.realpath(__file__))
while not src_dir.endswith("WeiboSpider"):
    src_dir = os.path.dirname(src_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

import youran
from youran import headers
from youran import db


def kuaidaili():
    # https://www.kuaidaili.com/free/inha/2/
    for i in range(1,100):
        url=f'https://www.kuaidaili.com/free/inha/{i}/'
        res=requests.get(url,headers=headers.mobile,timeout=10)
        trs=Selector(text=res.text).xpath('//tr').getall()[1:]
        pprint(f'source=kuaidaili  page={i} length={len(trs)}')
        for tr_text in trs:
            tds=Selector(text=tr_text).xpath('//td/text()').getall()
            # pprint(tds)
            # IP	PORT	匿名度	类型	位置	响应速度	最后验证时间
            ip=tds[0]+':'+tds[1]
            niming=tds[2]
            leixing=tds[3]
            location=tds[4]
            ping=tds[5]
            validate_time=tds[6]
            youran.db.proxy.add({'_id':ip,'ip':ip,'niming':niming,'leixing':leixing,'location':location,'ping':ping,'alive':'None','validate_time':validate_time,'score':1})
            print(ip,niming,leixing,location)
        time.sleep(45)

# def kuaidaili():
#     # https://www.kuaidaili.com/free/inha/2/
#     for i in range(1,100):
#         url=f'https://www.kuaidaili.com/free/inha/{i}/'
#         res=requests.get(url,headers=headers.pc)
#         trs=Selector(text=res.text).xpath('//tr').getall()
#         print(trs)
#         break

if __name__=='__main__':
    kuaidaili()
