from minio import Minio
import requests
import io
from minio.error import S3Error
import youran
import contextlib
import os

class Min:
    def __init__(self):
        self.minioClient = Minio(f'{youran.MINIOIP}:{youran.MINIOPort}',
                        access_key=os.environ.get('MINIO_ACCESS_KEY', 'minioadmin'),
                        secret_key=os.environ.get('MINIO_SECRET_KEY', 'minioadmin'),
                        secure=False)

    def make_bucket(self,name):
        try:
            self.minioClient.make_bucket(name)
            return 0,'success'
        except S3Error as err:
            return -1,repr(err)
    def save(self,bucket_name,name,content):
        # response = requests.get(url, headers=headers.mobile, stream=True,timeout=30,verify=False)
        result = self.minioClient.put_object(
            bucket_name, name, io.BytesIO(content), length=-1, part_size=10*1024*1024,
        )
        if result.object_name==name:
            return 0
    def save_weibo(self,name,content):
        IS_NEW_DAY,year,month,day,hour=youran.utils.isnewday()
        if name.startswith("imgs/") or name.startswith("avatar/"):
            imgs_dict=list(youran.db.states.find({'_id':f'imgs_count_{year}{month}{day}'}))
            if imgs_dict:
                imgs_dict=imgs_dict[0]
                imgs_dict['count']+=1
            else:
                imgs_dict={'count':1,'_id':f'imgs_count_{year}{month}{day}','name':'imgs_count','update_time':f'{year}{month}{day}'}
            youran.db.states.add(imgs_dict)
        if name.startswith("videos/"):
            videos_dict=list(youran.db.states.find({'_id':f'videos_count_{year}{month}{day}'}))
            if videos_dict:
                videos_dict=videos_dict[0]
                videos_dict['count']+=1
            else:
                videos_dict={'count':1,'_id':f'videos_count_{year}{month}{day}','name':'videos_count','update_time':f'{year}{month}{day}'}
            youran.db.states.add(videos_dict)
        return self.save('weibo',name,content)
    def get_img(self,bucket_name,name):
        """
        安全获取对象数据，确保资源正确关闭
        """
        try:
            with contextlib.closing(self.minioClient.get_object(bucket_name, name)) as response:
                return response.data
        except S3Error as err:
            youran.logger.error(f"MinIO错误: {repr(err)}")
            return None
        except Exception as e:
            youran.logger.error(f"获取对象错误: {repr(e)}")
            return None
    def get_weibo_media(self,ttype,name):
        return self.get_img('weibo',f'{ttype}/'+name)

    def exist(self,name,t='imgs'):
        try:
            self.minioClient.stat_object('weibo', t+'/'+name)
            return True
        except Exception as e:
            return False 
    def count_weibo_imgs(self):
        file_count = sum(1 for _ in self.minioClient.list_objects('weibo', prefix='imgs/'))
        return file_count
    def count_weibo_videos(self):
        file_count = sum(1 for _ in self.minioClient.list_objects('weibo', prefix='videos/'))
        return file_count
if __name__=='__main__':
    m=Min()
    rr=m.make_bucket('weibo')
    print(rr)
    # rr=m.get_weibo_img('473ed7c0gy1fvwjohh750j20qo1bg7aj.jpg')
    # print(rr)
    # result=rr.save('https://img-cdn-qiniu.dcloud.net.cn/uniapp/doc/create1.png','test','imgs/create1.png')
    # # print(result)
    # List all object paths in bucket that begin with my-prefixname.
    objects = m.minioClient.list_objects('weibo', prefix='imgs/',
                                recursive=True)
    # print(objects)
    for obj in objects:
        print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
            obj.etag, obj.size, obj.content_type)
        break
    