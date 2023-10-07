import youran
from youran import db,net,utils

while True:
    IS_NEW_DAY,year,month,day,hour=youran.utils.isnewday()
    # if IS_NEW_DAY:
    count=youran.utils.db.mblog.counts({})
    authors=youran.utils.db.user.counts({})
    youran.db.states.add({'_id':f'user_count_{year}{month}{day}','name':'user_count','update_time':f'{year}{month}{day}','count':authors})
    youran.db.states.add({'_id':f'mblog_count_{year}{month}{day}','name':'mblog_count','update_time':f'{year}{month}{day}','count':count})
    youran.logger.warning(f'每日更新完成，时间：{year}:{month}:{day}')
    youran.utils.sleep(23*60*60,24*60*60)