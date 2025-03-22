import requests
from scrapy.selector import Selector
import time, pymongo, random
import sys, os
from pprint import pprint
import concurrent.futures
import threading

import youran.utils

# 获取根目录路径
src_dir = os.path.dirname(os.path.realpath(__file__))
while not src_dir.endswith("WeiboSpider"):
    src_dir = os.path.dirname(src_dir)
if src_dir not in sys.path:
    sys.path.append(src_dir)

import youran
from youran import headers
from youran import db

# 线程锁，防止并发问题
proxy_lock = threading.Lock()

def validate_proxy(proxy_ip, timeout=5):
    """
    验证代理IP是否可用
    
    Args:
        proxy_ip: 代理IP地址，格式为 "ip:port"
        timeout: 超时时间(秒)
        
    Returns:
        (bool, int): (是否可用, 响应时间(毫秒))
    """
    proxies = {
        "http": f"http://{proxy_ip}",
        "https": f"http://{proxy_ip}"
    }
    
    try:
        start_time = time.time()
        response = requests.get(
            "https://www.baidu.com", 
            proxies=proxies, 
            timeout=timeout,
            headers=headers.mobile
        )
        response_time = int((time.time() - start_time) * 1000)  # 毫秒
        
        if response.status_code == 200:
            youran.logger.info(f"代理 {proxy_ip} 验证成功，响应时间: {response_time}ms")
            return True, response_time
        else:
            youran.logger.warning(f"代理 {proxy_ip} 返回状态码: {response.status_code}")
            return False, 0
            
    except Exception as e:
        youran.logger.warning(f"代理 {proxy_ip} 验证失败: {str(e)}")
        return False, 0

def kuaidaili(max_pages=20):
    """
    从快代理获取免费代理IP
    
    Args:
        max_pages: 最大抓取页数
    """
    import json
    
    # 随机化页数范围，避免被检测
    pages = list(range(1, max_pages + 1))
    random.shuffle(pages)
    
    for i in pages:
        url = f'https://www.kuaidaili.com/free/inha/{i}/'
        
        try:
            # 添加随机User-Agent
            current_headers = headers.mobile.copy()
            current_headers['User-Agent'] = random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
            ])
            
            # 添加随机延迟，避免被封
            delay = random.randint(30, 60)
            youran.logger.info(f"等待 {delay} 秒后抓取页面{i}...")
            youran.utils.sleep(0,delay)
            
            res = requests.get(url, headers=current_headers, timeout=15)
            
            # 检查是否被封
            if "访问频率过高" in res.text or res.status_code != 200:
                youran.logger.warning(f"页面 {i} 访问受限，等待更长时间...")
                time.sleep(random.uniform(120, 180))  # 更长的等待时间
                continue
                
            lines = res.text.split('\n')
            proxy_count = 0
            
            for line in lines:
                if line.startswith('const fpsList ='):
                    line = line.replace('const fpsList =', '')[:-1]
                    items = json.loads(line)
                    
                    # 使用线程池并行验证代理
                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                        futures = []
                        
                        for item in items:
                            proxy_ip = f"{item['ip']}:{item['port']}"
                            futures.append(executor.submit(
                                process_proxy, 
                                proxy_ip, 
                                item['location'], 
                                item['speed'], 
                                item['last_check_time']
                            ))
                            
                        # 等待所有验证完成
                        for future in concurrent.futures.as_completed(futures):
                            result = future.result()
                            if result:
                                proxy_count += 1
                                
            youran.logger.info(f"页面 {i} 成功添加 {proxy_count} 个代理")
            
        except Exception as e:
            youran.logger.error(f"抓取页面 {i} 时出错: {repr(e)}")
            time.sleep(random.uniform(60, 90))  # 出错后等待更长时间

def process_proxy(proxy_ip, location, speed, validate_time):
    """处理单个代理IP的验证和添加"""
    # 验证代理
    is_valid, response_time = validate_proxy(proxy_ip)
    
    if is_valid:
        # 使用实际测量的响应时间
        ping = response_time if response_time > 0 else speed
        
        # 添加到数据库
        with proxy_lock:
            youran.db.proxy.add({
                '_id': proxy_ip,
                'ip': proxy_ip,
                'niming': 'niming',
                'leixing': 'leixing',
                'location': location,
                'ping': ping,
                'alive': 'Yes',  # 标记为有效
                'validate_time': validate_time,
                'score': 1
            })
            
        youran.logger.info(f"添加有效代理: {proxy_ip}, 位置: {location}, 响应时间: {ping}ms")
        return True
    else:
        youran.logger.warning(f"跳过无效代理: {proxy_ip}")
        return False

if __name__ == '__main__':
    kuaidaili(max_pages=30)
