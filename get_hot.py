
import youran,time
from youran import db,net,utils
from youran.db import *

while True:
    text_herfs=net.hot.get()
    items=[(hot[0],hot[1]) for hot in text_herfs]
    if db.hot.add({'items':items}):
        # logger.warning('更新当前热点成功：')
        youran.logger.warning(items)
    for text,herf in text_herfs:
        url,bids=net.hot.get_detail(herf)
        youran.logger.warning(f'热点链接：{url},bids:{bids}')
        if bids:
            db.hotid.add({'url':url,'bids':bids})
            for bid in bids:
                if bid:
                    utils.download_mblog({'bid':bid,'isLongText':True},'uid','current_page','total_page',duplicate=False,proxy=True)
                    utils.sleep(5, 10)

    youran.db.states.add({'name':'热搜：','update_time':time.asctime( time.localtime(time.time()) )})
    utils.sleep(10*60,30*60)
