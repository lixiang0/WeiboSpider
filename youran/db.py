import os
from abc import ABC, abstractclassmethod, abstractmethod
import random,time
import pymongo
import youran

db_client = pymongo.MongoClient(f"mongodb://{youran.DBIP}:{youran.DBPort}/")["db_weibo"]
db_proxy = pymongo.MongoClient(f"mongodb://{youran.DBIP}:{youran.DBPort}/")["db_proxy"]


class BaseDB():
    def __init__(self,name) -> None:
        self.db=db_client[name]
    
    def update(self,flt,kvs):
        try:
            self.db.update(flt, {'$set': kvs}, upsert=True)
            return True
        except pymongo.errors.DuplicateKeyError:
            return False

    
    def find(self,kv):
        return self.db.find(kv)


    def delete(self,kv):
        return self.db.delete_many(kv)

    # @abstractclassmethod    
    def count(self,kv):
        return self.db.count_documents(kv)
    def distinct(self,kv):
        return self.db.distinct(kv)
    # @abstractclassmethod
    def exists(self,kv):
        return self.db.count_documents(kv)>0
    def random(self,size=10):
        # return list(self.db.find({}).limit(size).skip(int(random.random()*self.db.estimated_document_count())))
        return list(self.db.aggregate([{'$sample': {'size': size}}]))
    @abstractclassmethod
    def page(self):
        pass
class Comment(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_comments')

    def add(self, kvs):
        return self.update({'_id': kvs['_id']}, kvs)

class Account(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_count')

    def add(self, kvs):
        return self.update({'_id': kvs['_id']}, kvs)
    def find_user(self,uname):
        return list(self.find({'uname':uname}))

class Fav(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_fav')

    def add(self, kvs):
        return self.update({'_id': kvs['uid']+'$'+kvs['bid']}, kvs)
class Follow(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_follower')

    def add(self, kvs):
        return self.update({'_id': kvs['_id']}, kvs)


    def bloggers(self):
        return set([d['blogger'] for d in self.find({})])

    #找到所有的关注
    #_id=uid+blogger_id    fans:uid  blogger: blogger_id
    def find_follows(self,id=None,page=0):
        flts={}
        if id:
            flts={'_id':{'$regex':f'^{id}[0-9]+'}}
        return list(self.find(flts).skip(int(page*20)).limit(20))

class Hot(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_hot')

    def add(self, kvs):
        return self.update({'_id': time.time()}, kvs)

    def find_hot_items(self):
        cur=self.find({})
        if cur and cur.count():
            _=cur.sort('_id', direction=-1).next()
            # print(_)
            return _['items']
        else:
            return []
    def find_hot_ids(self):
        cur=self.find({})
        if cur and cur.count():
            _=cur.sort('_id', direction=-1).next()
            # print(_)
            return _['_id']
        else:
            return []
class HotID(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_hotids')

    def add(self, kvs):
        return self.update({'_id': kvs['url']}, kvs)

class Log(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_log')

    def add(self, kvs):
        return self.update({'_id': kvs['_id']},kvs)
     

class Mblog(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_mblogs')

    def add(self, kvs):
        return self.update({'_id': kvs['_id']}, kvs)

    def counts(self):
        return self.count({})

    def page(self,ids,page=0):
        result=self.find({"uid": {"$in": [int(id) for id in ids]}}).sort('created_at1', direction=-1).skip(int(page*20)).limit(20)
        return result
    def current_page(self,id):
        self.distinct({'uid':id})/20

    def bids(self,bids):
        return list(self.find({"bid": {"$in": bids}}).sort('_id', direction=-1))
class Proxy(BaseDB):
    def __init__(self) -> None:
        self.db=db_proxy['db_proxy']
    def add(self, kvs):
        return self.update({'_id': kvs['_id']}, kvs)
    
    def get_randomip(self):
        # print(self.random(2))
        ip=list(self.random(2))[0]

        if 'https' in ip['niming']:
            return {'https': f"https://{ip['ip']}"}
        else:
            return {'http': f"http://{ip['ip']}"}
class States(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_states')

    def add(self, kvs):
        return self.update({'_id': kvs['name']}, kvs)
    

class User(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_user')

    def add(self, kvs):
        return self.update({'_id': kvs['_id']}, kvs)

    def find_users(self,ids,page=0):
        return list(self.find({"_id": {"$in": ids}}).sort('uid', direction=-1).skip(int(page*20)).limit(20))
comment=Comment()
account=Account()
user=User()
fav=Fav()
follow=Follow()
hot=Hot()
hotid=HotID()
log=Log()
mblog=Mblog()
states=States()
proxy=Proxy()

if __name__=='__main__':
    print('测试：')

    # assert comment.add({'_id':'4694520925260752'}) is True
    # assert comment.find({'_id':'4694520925260752'}).next()=={'_id': '4694520925260752'}
    # assert comment.count({'_id':'4694520925260752'})==1
    # assert comment.exists({'_id':'4694520925260752'})==True

    # assert account.add({'_id':'4694520925260752'}) is True
    # assert account.find({'_id':'4694520925260752'}).next()=={'_id': '4694520925260752'}
    # assert account.count({'_id':'4694520925260752'})==1
    # assert account.exists({'_id':'4694520925260752'})==True


    # assert user.add({'uid':'1','bid':'2'}) is True
    # assert user.find({'uid':'1'}).next()=={'_id': '1$2', 'bid': '2', 'uid': '1'}
    # assert user.count({'uid':'1'})==1
    # assert user.exists({'uid':'1'})==True
    print(mblog.counts())
  