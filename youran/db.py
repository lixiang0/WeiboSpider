import os
from abc import ABC, abstractclassmethod, abstractmethod
import random, time
import pymongo
import youran
from functools import wraps
from contextlib import contextmanager

# 从环境变量获取数据库凭证，如果不存在则使用默认值
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASS = os.environ.get('DB_PASS', '123456')
DB_HOST = os.environ.get('DB_HOST', youran.DBIP)
DB_PORT = os.environ.get('DB_PORT', youran.DBPort)
MAX_POOL_SIZE = 50
MIN_POOL_SIZE = 10

# 创建带连接池的 MongoDB 客户端
_client = pymongo.MongoClient(
    f"mongodb://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/",
    maxPoolSize=MAX_POOL_SIZE,
    minPoolSize=MIN_POOL_SIZE,
    retryWrites=True,
    socketTimeoutMS=30000,
    connectTimeoutMS=20000,
    serverSelectionTimeoutMS=20000
)

# 使用单一客户端实例来获取不同的数据库
db_client = _client["db_weibo"]
db_proxy = _client["db_proxy"]
db_liuyan = _client["db_liuyan"]
media_urls = _client["media_urls"]

# 定义装饰器用于错误处理
def db_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except pymongo.errors.PyMongoError as e:
            youran.logger.error(f"数据库操作错误: {repr(e)}")
            if isinstance(e, pymongo.errors.AutoReconnect):
                youran.logger.warning("尝试重新连接数据库...")
                time.sleep(1)  # 避免立即重试
                try:
                    return func(*args, **kwargs)
                except Exception as retry_e:
                    youran.logger.error(f"重试失败: {repr(retry_e)}")
            return None
    return wrapper

class BaseDB():
    def __init__(self, name) -> None:
        self.db = db_client[name]
        
    @db_error_handler
    def update(self, flt, kvs):
        try:
            result = self.db.update_one(flt, {'$set': kvs}, upsert=True)
            return result.acknowledged
        except pymongo.errors.DuplicateKeyError:
            youran.logger.warning(f"插入重复键: {flt}")
            return False
            
    @db_error_handler
    def add(self, kvs):
        return self.update({'_id': kvs['_id']}, kvs)
    
    @db_error_handler
    def find(self, kv, projection=None, sort_key=None, sort_direction=-1, limit=0):
        query = self.db.find(kv, projection)
        if sort_key:
            query = query.sort(sort_key, sort_direction)
        if limit > 0:
            query = query.limit(limit)
        return query

    @db_error_handler
    def delete(self, kv):
        result = self.db.delete_many(kv)
        return result.deleted_count if result else 0

    @db_error_handler
    def counts(self, kv=None):
        kv = kv or {}
        return self.db.count_documents(kv)
    
    @db_error_handler
    def distinct(self, field, filter=None):
        filter = filter or {}
        return self.db.distinct(field, filter)
    
    @db_error_handler
    def exists(self, kv):
        return self.db.count_documents(kv, limit=1) > 0
        
    @db_error_handler
    def random(self, size=10):
        """
        获取随机文档，使用高效的聚合操作
        
        Args:
            size: 要返回的文档数量
            
        Returns:
            随机文档列表
        """
        try:
            # 使用MongoDB的$sample聚合操作，这比skip+limit更高效
            pipeline = [{'$sample': {'size': size}}]
            return list(self.db.aggregate(pipeline, allowDiskUse=True))
        except Exception as e:
            youran.logger.error(f"随机查询错误: {repr(e)}")
            # 如果聚合操作失败，回退到旧方法
            count = self.db.estimated_document_count()
            if count == 0:
                return []
            skip = int(random.random() * count)
            if skip + size > count:
                skip = max(0, count - size)
            return list(self.db.find({}).limit(size).skip(skip))
            
    @abstractmethod
    def page(self, page=0, size=20, sort_key='_id', direction=-1, filter=None):
        """
        通用分页方法
        
        Args:
            page: 页码（从0开始）
            size: 每页大小
            sort_key: 排序字段
            direction: 排序方向 (1=升序, -1=降序)
            filter: 过滤条件
            
        Returns:
            查询结果列表
        """
        filter = filter or {}
        return list(self.db.find(filter).sort(sort_key, direction).skip(page * size).limit(size))

class Comment(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_comments')
    def add(self,kvs):
        IS_NEW_DAY,year,month,day,hour=youran.utils.isnewday()
        comment_dict=list(youran.db.states.find({'_id':f'comment_count_{year}{month}{day}'}))
        if comment_dict:
            comment_dict=comment_dict[0]
            comment_dict['count']+=1
        else:
            comment_dict={'count':1,'_id':f'comment_count_{year}{month}{day}','name':'comment_count','update_time':f'{year}{month}{day}'}
        youran.db.states.add(comment_dict)
        return self.update({'_id':kvs['_id']},kvs)

class Account(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_count')

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
    def bloggers(self):
        return set([d['blogger'] for d in self.find({})])

    #找到所有的关注
    #_id=uid+blogger_id    fans:uid  blogger: blogger_id
    def find_follows(self,id=None,page=-1):
        flts={}
        if id:
            flts={'_id':{'$regex':f'^{id}[0-9]+'}}
        if page == -1:
            return list(self.find(flts))
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
            return _['items']
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
     

class Mblog(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_mblogs')

    def add(self,kvs):
        IS_NEW_DAY,year,month,day,hour=youran.utils.isnewday()
        mblog_dict=list(youran.db.states.find({'_id':f'mblog_count_{year}{month}{day}'}))
        if mblog_dict:
            mblog_dict=mblog_dict[0]
            mblog_dict['count']+=1
        else:
            mblog_dict={'count':1,'_id':f'mblog_count_{year}{month}{day}','name':'mblog_count','update_time':f'{year}{month}{day}'}
        youran.db.states.add(mblog_dict)
        return self.update({'_id':kvs['_id']},kvs)

    def page(self,ids=None,page=0,direction=-1,num=20):
        if ids is None:
            result=self.find({}).sort('created_at1', direction=direction).skip(int(page*num)).limit(num)
            return result
        result=self.find({"uid": {"$in": [int(id) for id in ids]}}).sort('created_at1', direction=direction).skip(int(page*num)).limit(num)
        return result
    def current_page(self,id):
        self.distinct({'uid':id})/20

    def bids(self,bids):
        return list(self.find({"bid": {"$in": bids}}).sort('_id', direction=-1))
class Proxy(BaseDB):
    def __init__(self) -> None:
        self.db=db_proxy['db_proxy']

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

class User(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_user')
    def add(self,kvs):
        IS_NEW_DAY,year,month,day,hour=youran.utils.isnewday()
        user_dict=list(youran.db.states.find({'_id':f'user_count_{year}{month}{day}'}))
        if user_dict:
            user_dict=user_dict[0]
            user_dict['count']+=1
        else:
            user_dict={'count':1,'_id':f'user_count_{year}{month}{day}','name':'user_count','update_time':f'{year}{month}{day}'}
        youran.db.states.add(user_dict)
        return self.update({'_id':kvs['_id']},kvs)
    def find_users(self,ids,page=0):
        return list(self.find({"_id": {"$in": ids}}).sort('uid', direction=-1).skip(int(page*20)).limit(20))

class Liuyan(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_liuyan')

class Tongji(BaseDB):
    def __init__(self) -> None:
        super().__init__('db_tongji')

class MediaUrls(BaseDB):
    def __init__(self) -> None:
        super().__init__('media_urls')
    
    def find_pending(self, limit=100, days=None):
        """
        查找状态为pending的媒体URL
        
        Args:
            limit: 最大返回数量
            days: 只返回最近几天的媒体
            
        Returns:
            符合条件的媒体记录列表
        """
        query = {'download_status': 'pending'}
        
        # 添加时间过滤
        if days:
            import time
            from datetime import datetime, timedelta
            
            cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
            query['add_time'] = {'$gte': cutoff_time}
            
        # 构建查询并限制结果数量
        cursor = self.find(query, sort_key='add_time', sort_direction=1)
        if limit > 0:
            cursor = cursor.limit(limit)
            
        return list(cursor)
        
    def find_by_status(self, status, limit=100):
        """
        根据下载状态查找媒体URL
        
        Args:
            status: 下载状态 (pending, success, failed, skipped)
            limit: 最大返回数量
            
        Returns:
            符合条件的媒体记录列表
        """
        return list(self.find({'download_status': status}, sort_key='add_time', limit=limit))
        
    def find_by_bid(self, bid, limit=100):
        """
        查找特定微博ID的媒体URL
        
        Args:
            bid: 微博ID
            limit: 最大返回数量
            
        Returns:
            符合条件的媒体记录列表
        """
        return list(self.find({'bid': bid}, sort_key='add_time', limit=limit))
        
    def find_by_uid(self, uid, limit=100):
        """
        查找特定用户ID的媒体URL
        
        Args:
            uid: 用户ID
            limit: 最大返回数量
            
        Returns:
            符合条件的媒体记录列表
        """
        return list(self.find({'uid': uid}, sort_key='add_time', limit=limit))
        
    def update_status(self, media_id, status, file_path=None):
        """
        更新媒体下载状态
        
        Args:
            media_id: 媒体记录ID
            status: 新状态 (pending, success, failed, skipped)
            file_path: 可选的文件路径
            
        Returns:
            更新是否成功
        """
        update = {
            'download_status': status,
            'download_time': time.time()
        }
        
        if status == 'failed':
            # 使用findAndModify操作来原子性地增加重试计数
            try:
                result = self.db.find_one_and_update(
                    {'_id': media_id},
                    {'$inc': {'retry_count': 1}, '$set': update},
                    return_document=True
                )
                return result is not None
            except Exception as e:
                youran.logger.error(f"更新媒体状态出错: {repr(e)}")
                return False
                
        if file_path:
            update['file_path'] = file_path
            
        return self.update({'_id': media_id}, update)

    def batch_update_status(self, media_ids, status):
        """
        批量更新媒体下载状态
        
        Args:
            media_ids: 媒体记录ID列表
            status: 新状态 (pending, success, failed, skipped)
            
        Returns:
            更新的记录数量
        """
        if not media_ids:
            return 0
            
        result = self.db.update_many(
            {'_id': {'$in': media_ids}},
            {'$set': {
                'download_status': status,
                'download_time': time.time()
            }}
        )
        
        return result.modified_count if result else 0
        
    def get_stats(self):
        """
        获取媒体URL的统计信息
        
        Returns:
            包含各状态数量的字典
        """
        stats = {
            'total': self.counts(),
            'pending': self.counts({'download_status': 'pending'}),
            'success': self.counts({'download_status': 'success'}),
            'failed': self.counts({'download_status': 'failed'}),
            'skipped': self.counts({'download_status': 'skipped'})
        }
        return stats
        
    def clean_failed(self, max_retries=3):
        """
        清理失败次数超过阈值的记录，将状态设为skipped
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            更新的记录数
        """
        result = self.db.update_many(
            {'download_status': 'failed', 'retry_count': {'$gte': max_retries}},
            {'$set': {'download_status': 'skipped'}}
        )
        return result.modified_count if result else 0
        
    def get_media_types_count(self):
        """
        获取各种媒体类型的数量统计
        
        Returns:
            包含各类型数量的字典
        """
        pipeline = [
            {'$group': {
                '_id': '$media_type',
                'count': {'$sum': 1}
            }}
        ]
        
        try:
            result = list(self.db.aggregate(pipeline))
            stats = {}
            for item in result:
                stats[item['_id']] = item['count']
            return stats
        except Exception as e:
            youran.logger.error(f"聚合媒体类型统计出错: {repr(e)}")
            return {}
            
    def get_user_media_counts(self, limit=10):
        """
        获取拥有最多媒体的用户统计
        
        Args:
            limit: 返回的用户数量
            
        Returns:
            用户媒体统计列表
        """
        pipeline = [
            {'$group': {
                '_id': '$uid',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]
        
        try:
            return list(self.db.aggregate(pipeline))
        except Exception as e:
            youran.logger.error(f"聚合用户媒体统计出错: {repr(e)}")
            return []
            
    def reset_failed(self, max_retry_count=None):
        """
        重置失败的下载记录为待下载状态
        
        Args:
            max_retry_count: 如果指定，只重置重试次数小于该值的记录
            
        Returns:
            更新的记录数
        """
        query = {'download_status': 'failed'}
        
        if max_retry_count is not None:
            query['retry_count'] = {'$lt': max_retry_count}
            
        result = self.db.update_many(
            query,
            {'$set': {'download_status': 'pending'}}
        )
        
        return result.modified_count if result else 0
        
    def find_recently_added(self, days=1, limit=100):
        """
        查找最近添加的媒体记录
        
        Args:
            days: 最近几天
            limit: 最大返回数量
            
        Returns:
            媒体记录列表
        """
        from datetime import datetime, timedelta
        
        cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
        query = {'add_time': {'$gte': cutoff_time}}
        
        return list(self.find(query, sort_key='add_time', sort_direction=-1, limit=limit))

    def page(self, page=0, size=20, sort_key='add_time', direction=-1, filter=None):
        """
        分页获取媒体记录
        
        Args:
            page: 页码（从0开始）
            size: 每页大小
            sort_key: 排序字段
            direction: 排序方向 (1=升序, -1=降序)
            filter: 过滤条件
            
        Returns:
            当前页的媒体记录
        """
        filter = filter or {}
        return list(self.find(filter, sort_key=sort_key, sort_direction=direction).skip(page * size).limit(size))

tongji=Tongji()
liuyan=Liuyan()
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
media_urls=MediaUrls()

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
  