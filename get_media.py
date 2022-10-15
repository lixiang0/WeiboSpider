# -*- coding: utf-8 -*-
import os
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
import logging,time
from youran.disks import Min
from tqdm import tqdm
import pika
import json,io
main = logging.getLogger('main')
main.setLevel(logging.DEBUG)

mm=Min()

while True:
    mblogs = list(youran.db.mblog.random(100))
    with tqdm(total=len(mblogs),postfix=dict,mininterval=0.3) as pbar:
        for mblog in mblogs:
            if float(mblog['spider_time'])>1627211116.:
                # pbar.update(1)
                continue
            try:
                # mblog['isLongText']=True
                # mblog['duplicate']=True
                # b=json.dumps(mblog).encode()
                # channel.basic_publish(exchange='', routing_key='mblogs', body=b)
                import send
                mblog['duplicate']=False
                send.send(mblog)
                youran.db.states.add({'name':'update_medias','update_time':time.asctime( time.localtime(time.time()) )})
                # print(" [x] Sent from get_media.py!'")
                time.sleep(5)
            except Exception as e:
                main.error('error.....retry download............')
                main.error(repr(e))
            pbar.update(1)

