import os
#默认无密码
DBIP = os.environ['DBIP']
MINIOIP = os.environ['MINIOIP']
DBPort = os.environ['DBPort']
MINIOPort = os.environ['MINIOPort']


import logging
logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%b %d %Y %H:%M:%S',
                            level=logging.DEBUG
                            )
logger = logging.getLogger('main')
logger.setLevel(logging.DEBUG)

def config():
    duplicate=False
    cookie=False
    proxy=False

