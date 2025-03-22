
import os
os.environ["DBIP"]="192.168.8.111"
os.environ["MINIOIP"]="192.168.8.111"
os.environ["DBPort"]="27017"
os.environ["MINIOPort"]="9000"

import youran
from youran.proxy import kuaidaili
while True:
    kuaidaili()
    youran.utils.sleep(23*60*60,24*60*60)