import os
#默认无密码
os.environ['DBIP']='192.168.1.9'
os.environ['MINIOIP']='192.168.1.9'
os.environ['DBPort']='27017'
os.environ['MINIOPort']='9010'
DBIP = os.environ['DBIP']
MINIOIP = os.environ['MINIOIP']
DBPort = os.environ['DBPort']
MINIOPort = os.environ['MINIOPort']