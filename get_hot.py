# import os
# os.environ['DBIP']='192.168.1.123'
# os.environ['MINIOIP']='192.168.31.13'
# os.environ['DBPort']='27017'
# os.environ['MINIOPort']='9010'

import youran,time
from youran import db,net,utils
from youran.db import *


# print(list(db.hot.find_hot('')))
while True:
    utils.download_hot()
    youran.db.states.add({'name':'热搜：','update_time':time.asctime( time.localtime(time.time()) )})
    utils.sleep(10*60,30*60)
