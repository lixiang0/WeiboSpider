

# [悠然微博](http://1.14.73.45:18089/)：微博爬虫、微博本地化部署

## 【文档不完善，继续补充中。】

## 20231007更新v0.2.0

- 更新UI:about中新增每日博文和博主数
- 完善爬取逻辑：
  - 随机爬取全站每个用户前5页
  - 定时抓取我的关注博主的博文(使用cookie)
  - 定时更新热搜
  - 从评论中抓取全站用户信息，以保证抓取到的是活跃用户
  - 每天抓取最新一次代理IP
  - 每天做一次用户和博文的统计

## 20221015更新

- 更新UI
- 完善爬取逻辑

## 主要功能：

- 爬取全站微博
- 抓取全站博主信息
- 实时抓取全站热搜
- 本地化部署微博
- 关注博主/搜索博主/收藏博文

## 功能展示

- 用户主页

![](imgs/用户主页.png)

- 个人主页

![](imgs/个人主页.png)

- 关注页

![](imgs/关注页.png)

- 博文页

![](imgs/博文页.png)

- 搜索博主

![](imgs/搜索博主.png)

- 随机博文

![](imgs/随机博文.png)



## todo

- 完善文档

## 功能

## docker部署

```
git clone https://github.com/lixiang0/WeiboSpider
cd WeiboSpider/

# 1.minio
docker run \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio1 \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=minio" \
  -v /mnt/data:/data \
  quay.io/minio/minio server /data --console-address ":9001"

# 2.[可选]关于cookie 
# https://github.com/moonD4rk/HackBrowserData
# cookie保存在results目录下

# 3.部署
# 注意docker-compose.yml里面的mongodb和minio的地址
sudo docker-compose up -d --build


