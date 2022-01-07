import json
mobile = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Mobile Safari/537.36',
'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
'accept-encoding': 'gzip, deflate, br',
'accept-language': 'en,zh-CN;q=0.9,zh;q=0.8',

}
cookies=dict()
import os
if os.path.exists('results/firefox_cookie.json'):
    keys=json.load(open('results/firefox_cookie.json'))['.weibo.cn']
    for k in keys:
        cookies[k['KeyName']]=k['Value']
else:
    cookies=None
    
pc={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/76.0.3809.100 Chrome/76.0.3809.100 Safari/537.36',
                       'Accept': '*/*',
                       'Accept-Encoding': 'gzip, deflate, br',
                       'Accept-Language': 'en,zh-CN;q=0.9,zh;q=0.8',
                       }
