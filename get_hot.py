
import youran,time
from youran import db,net,utils
from youran.db import *


# print(list(db.hot.find_hot('')))
while True:
    utils.download_hot()
    youran.db.states.add({'name':'hots','update_time':time.asctime( time.localtime(time.time()) )})
    utils.sleep(10*60,30*60)
