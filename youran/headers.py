import json,os
#博文的头
mobile = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Mobile Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
}
pc={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/76.0.3809.100 Chrome/76.0.3809.100 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
}
#头像的头
img = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Mobile Safari/537.36',
    'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',
    'referer': 'https://m.weibo.cn/'
}
video={'Host': 'f.video.weibocdn.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0',
        'Accept': 'video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': 'https://weibo.cn/',
        'Sec-Fetch-Dest': 'video',
        'Sec-Fetch-Mode': 'no-cors',
}
cookies=dict()
cookies['_T_WM']='c2dae04e7dc61854cbda0a86b9f6d8d8'
cookies['mweibo_short_token']='a063a5c2d7'
cookies['SUBP']='0033WrSXqPxfM725Ws9jqgMF55529P9D9WWdqm5.QclOH545ex2uKkmb5NHD95Qce0.7eKBXe0MXWs4Dqcj6i--ciKnEi-27i--NiKnXi-zci--Ri-88i-2pi--Ni-88iK.Ni--ciKLhi-iWi--Ri-2NiKnci--Ri-2NiKn4'
cookies['SUB']='_2A25IGGfQDeRhGeBN4lIQ9CrPzDiIHXVr4wmYrDV6PUJbktCOLXT1kW1NRAmEpHFnSVk7FiI7Ez5GLdMAM9uiuUlo'
