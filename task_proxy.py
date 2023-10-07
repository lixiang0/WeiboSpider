
import requests
from scrapy.selector import Selector
import time
import youran
from youran import headers,db

from youran.proxy import kuaidaili
# export DBIP=192.168.2.103 \
# export MINIOIP=192.168.2.107 \
# export DBPort=27017 \
# export MINIOPort=9010
import youran
from youran import db,net,utils
from youran.db import *
from youran.net import *
import os,logging,time,math
while True:
    kuaidaili()
    youran.utils.sleep(23*60*60,24*60*60)