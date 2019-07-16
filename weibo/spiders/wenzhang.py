import requests
from bs4 import BeautifulSoup
import re
import csv

url='https://weibo.com/p/1005052014433131/wenzhang'
# url='https://weibo.com/ttarticle/p/show?id=2309404389508454971885'
cookie = {'Cookie': ''}  # 将cookie替换成自己的cookie
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
                   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3'}
res = requests.get(url, headers=headers,cookies=cookie).content.decode('utf-8')
res=res.replace('\\\\','\\').replace('\/','/').replace('\\"','"').replace('\\t','').replace(r'\r\n','')
pattern=re.compile(r'Pl_Core_ArticleList__61_page=[0-9]+')
items =pattern.findall(res)[-2]
num_page=int(items[-2:])
urls=set()
for page in range(1,num_page+1):
    url=f"https://weibo.com/p/1005052014433131/wenzhang?cfs=600&Pl_Core_ArticleList__61_filter=&filter=&time=&type=&Pl_Core_ArticleList__61_page={page}#Pl_Core_ArticleList__61"
    res = requests.get(url, headers=headers,cookies=cookie).content.decode('utf-8')
    res=res.replace('\\\\','\\').replace('\/','/').replace('\\"','"').replace('\\t','').replace(r'\r\n','')
    pattern1=re.compile(r'/ttarticle/p/show\?id=[0-9]+')
    pattern2=re.compile(r'/p/[0-9]+\?mod=zwenzhang')
    items1 =set(pattern1.findall(res))
    items2 =set(pattern2.findall(res))
    urls=urls|items1|items2
    print(f'page:{page},items:{len(items1|items2)}')
print(f'num of item:{len(urls)}')
with open('唐史主任.csv', 'w',encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile, delimiter=' ',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
    for url in urls:
        url='https://weibo.com'+url
        res = requests.get(url, headers=headers,cookies=cookie).content
        soup=BeautifulSoup(res,"html.parser")
        title=soup.title.text
        items=soup.findAll('p')
        imgs=[]
        for img in soup.find_all('img'):#<img src="https://wx3.sinaimg.cn/large/7811cf6bly1g1cetf9oaej20lq0m6tuy.jpg">
            if '.sinaimg.cn/large/' in img['src']:
                imgs.append(img['src'])
        content=''
        for item in items:
            content+=item.text
        print(title)
        writer.writerow([url,title,content,imgs])