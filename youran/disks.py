from minio import Minio
import requests
import io
from minio.error import S3Error
import youran
class Min:
    def __init__(self):
        self.minioClient = Minio(f'{youran.MINIOIP}:{youran.MINIOPort}',
                        access_key='minioadmin',
                        secret_key='minioadmin',
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
        return self.save('weibo1',name,content)
    def get_img(self,bucket_name,name):
        # Get data of an object.
        response=None
        # try:
        response = self.minioClient.get_object(bucket_name, name)
        # Read data from response.
        return response.data
        # finally:
            # response.close()
            # response.release_conn()
    def get_weibo_media(self,ttype,name):
        return self.get_img('weibo1',f'{ttype}/'+name)
        
        

    def exist(self,name,t='imgs'):
        try:
            self.minioClient.stat_object('weibo1', t+'/'+name)
            return True
        except Exception as e:
            return False 

if __name__=='__main__':
    m=Min()
    rr=m.make_bucket('weibo1')
    print(rr)
    # rr=m.get_weibo_img('473ed7c0gy1fvwjohh750j20qo1bg7aj.jpg')
    # print(rr)
    # result=rr.save('https://img-cdn-qiniu.dcloud.net.cn/uniapp/doc/create1.png','test','imgs/create1.png')
    # # print(result)
    # List all object paths in bucket that begin with my-prefixname.
    objects = m.minioClient.list_objects('weibo1', prefix='imgs/',
                                recursive=True)
    # print(objects)
    for obj in objects:
        print(obj.bucket_name, obj.object_name.encode('utf-8'), obj.last_modified,
            obj.etag, obj.size, obj.content_type)
        break
    