import scrapy


class weiboSpider(scrapy.Spider):
    name = "weibo"
    cookie = {'_T_WM':'',
            'ALF':'',
             'SCF':'-.',
             'SUB':'',
             'SUBP':'',
             'SUHB':'',
             'SSOLoginState':''}  # 将cookie替换成自己的cookie
    writer=open('my_weibo.txt','a')
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',
                   'Accept': 'text / html, application / xhtml + xml, application / xml;q = 0.9,image/webp, * / *;q = 0.8'}
    def start_requests(self):
        urls = [
            'https://weibo.cn'
        ]
        for url in urls:
            yield scrapy.Request(url=url, headers=self.headers,cookies=self.cookie,callback=self.parse)

    def parse(self, response):
        page_num=0
        if response.xpath("//input[@name='mp']") == []:#这里处理微博为空的情况
            page_num = 1
        else:
            page_num = (int)(response.xpath("//input[@name='mp']")[0].attrib['value'])
        # https://weibo.cn/?page=2
        for i in range(1,page_num+1):#page 1-40
            yield response.follow(f'https://weibo.cn/?page={i}', callback=self.parse_id)

    def parse_id(self,response):
        ids=response.xpath('//div[contains(@id,"M_HC")]/@id').getall()
        for id in ids:#parse weibos
            #https://weibo.cn/comment/HAwmslrRT
            yield response.follow(f'https://weibo.cn/comment/{id.replace(r"M_","")}', callback=self.parse_weibo)

    def parse_weibo(self,response):
        content=response.xpath('//div[@id="M_"]')[0].xpath('string()').extract()[0]
        self.writer.write(content+'\n\n')