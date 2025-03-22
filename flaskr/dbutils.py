from re import T
from youran import db,utils,net



def get_hot():
    '''
    作用：返回当前的热搜。
    参数：
    return：如果热点为空，返回[],否则为热搜列表
    '''
    return db.hot.find_hot_items()
def get_hot_bids(url):
    '''
    作用：返回当前的热搜。
    参数：
    return：如果热点为空，返回[],否则为热搜列表
    '''
    cur= db.hotid.find({'url':url+'?type=grab&display=0&retcode=6102'})
    if cur and cur.count():
        return cur.next()['bids']
    else:
        return []
def get_user(uid):
    '''
    作用：返回对应uid的用户信息
    参数：uid
    return：用户信息，字典类型
    '''
    cur=db.user.find({'_id':int(uid)})
    if cur and cur.count():
        return cur.next()
    else:
        return None
def get_users(uids):
    '''
    作用：返回对应uid列表的用户信息
    参数：uid
    return：用户信息列表，list
    '''
    infos=db.user.find_users(uids)
    if infos:
        return infos
    else:
        return None

def get_follows(uid):
    '''
    作用：返回对应uid的关注信息
    参数：uid
    return：关注列表，list
    '''
    return list(db.follow.find_follows(int(uid)))
def is_follow(uid,fuid):
    _={'_id': str(uid)+str(fuid), 'fans': int(uid), 'blogger': int(fuid)}
    cur=db.follow.find(_)
    if cur and cur.count():
        return True
    else:
        return False
def add_follow(uid,fuid):
    _={'_id': str(uid)+str(fuid), 'fans': int(uid), 'blogger': int(fuid)}
    return db.follow.add(_)
def del_follow(uid,fuid):
    _={'_id': str(uid)+str(fuid), 'fans': int(uid), 'blogger': int(fuid)}
    return db.follow.delete(_)
def get_page(ulist,pagenum):
    '''
    作用：返回对应uid列表的pagenum页码的微博，微博以时间倒序。
    参数：uid列表，页码
    return：微博列表
    '''
    return list(db.mblog.page(ulist,pagenum))
def random_blog(num):
    '''
    作用：返回随机num数目的微博
    参数：num
    return：微博列表，list
    '''
    return db.mblog.random(int(num))
def random_user(num):
    '''
    作用：返回随机num数目的用户
    参数：num
    return：随机的用户列表，list
    '''
    return db.user.random(int(num))

def get_mblog_bid(bid):
    cur= db.mblog.find({'bid':bid})
    if cur and cur.count():
        return cur.next()
    else:
        return None
def get_mblog_bids(bids):
    mblogs= db.mblog.bids(bids)
    return mblogs
def get_comment(id):
    cur=db.comment.find({'_id':id})
    if cur and cur.count():
        return cur.next()
    else:
        return None

def is_fav(uid,bid):
    cur=db.fav.find({'uid':uid,'bid':bid})
    if cur and cur.count():
        return True
    else:
        return False
def add_fav(uid,bid):
    db.fav.add({'uid':uid,'bid':bid})
def del_fav(uid,bid):
    db.fav.delete({'uid':uid,'bid':bid})
def get_fav(uid):
    cur=db.fav.find({'uid':uid})
    if cur and cur.count():
        return list(cur)
    else:
        return []

def add_liuyan(kvs):
    db.liuyan.add(kvs)

def find_liuyan():
    return db.liuyan.find({}).sort('_id', direction=-1)

def add_count(kv):
    kvs=list(db.tongji.find({'_id':kv['filename']}))
    if kvs and len(kvs)>0:
        kv['count']=kvs[0]['count']+1
        db.tongji.add(kv)
    else:
        kv['_id']=kv['filename']
        kv['count']=1
        db.tongji.add(kv)
    

def find_count(kv):
    return db.tongji.find(kv)#.sort('_id', direction=-1)