# -*- coding: utf-8 -*-
import os
os.environ['DBIP']='192.168.1.14'
os.environ['MINIOIP']='192.168.1.9'
os.environ['DBPort']='27017'
os.environ['MINIOPort']='9010'
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
# handler = logging.FileHandler(f'logs/media.log', mode='w+')
# handler.setFormatter(logging.Formatter('%(levelname)s - %(asctime)s - %(message)s'))
# main.addHandler(handler)
mm=Min()
# connection = pika.BlockingConnection(
#     pika.ConnectionParameters(host='localhost'))
# channel = connection.channel()

# channel.queue_declare(queue='mblogs')
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
                # main.error(repr(e))
                # download(mblog)
            # pbar.set_postfix(**{'total'    : total_loss / (iteration + 1), 
            #                         'rpn_loc'  : rpn_loc_loss / (iteration + 1),  
            #                         'rpn_cls'  : rpn_cls_loss / (iteration + 1), 
            #                         'roi_loc'  : roi_loc_loss / (iteration + 1), 
            #                         'roi_cls'  : roi_cls_loss / (iteration + 1), 
            #                         'lr'       : get_lr(optimizer)})
            pbar.update(1)
    #break


                # url_names = net.comments.extract_img(comments)
                # main.warning(f'解析原微博评论图片：{url_names}')
                # for (url, name) in url_names:
                #     min.save_weibo('imgs/'+name, net.download(url))
    
