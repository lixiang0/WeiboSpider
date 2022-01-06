

# [悠然微博](http://122.51.50.206:8088)：微博爬虫、微博本地化部署

## 【文档不完善，继续补充中。】

## 功能：

- 爬取全站微博
- 抓取全站博主信息
- 实时抓取全站热搜
- 本地化部署微博

## todo
- 完善网页界面
- 完善文档

## docker部署

```
git clone https://github.com/lixiang0/weibo
cd weibo/

# 1.mongo
docker run -p 27017:27017 --name docker_mongodb -d mongo

# 2.minio
docker run \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio1 \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=minio" \
  -v /mnt/data:/data \
  quay.io/minio/minio server /data --console-address ":9001"

# 3.[可选]关于cookie 
# https://github.com/moonD4rk/HackBrowserData
# cookie保存在results目录下

# 4.部署
# 注意docker-compose.yml里面的mongodb和minio的地址
sudo docker-compose up -d --build
```

## [待补充]


## 截图

![](1634055603(1).png)

