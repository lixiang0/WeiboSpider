#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
# 环境变量设置
os.environ["DBIP"] = os.environ.get("DBIP", "192.168.8.111")
os.environ["MINIOIP"] = os.environ.get("MINIOIP", "192.168.8.111")
os.environ["DBPort"] = os.environ.get("DBPort", "27017")
os.environ["MINIOPort"] = os.environ.get("MINIOPort", "9000")

import sys
import time
import argparse
import logging
import random
from logging.handlers import RotatingFileHandler
from datetime import datetime
import os.path

# 添加项目根目录到sys.path，确保能正确导入youran模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import youran
from youran import utils, net, db, disks
from youran.disks import Min
min = Min()

# 配置日志
def setup_logger(log_file='media_downloader.log', level=logging.INFO, max_size=10*1024*1024, backup_count=5):
    """
    设置日志记录器
    
    Args:
        log_file: 日志文件名
        level: 日志级别
        max_size: 单个日志文件最大大小（字节）
        backup_count: 保留的日志文件数量
        
    Returns:
        配置好的logger实例
    """
    # 创建日志目录
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    log_path = os.path.join(log_dir, log_file)
    
    # 创建logger
    logger = logging.getLogger('media_downloader')
    logger.setLevel(level)
    
    # 清除已存在的处理器，避免重复
    if logger.handlers:
        logger.handlers = []
    
    # 创建文件处理器，使用RotatingFileHandler进行日志轮转
    file_handler = RotatingFileHandler(
        log_path, 
        maxBytes=max_size, 
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    
    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 初始化日志记录器
logger = setup_logger()

def get_media_urls(status='pending', limit=None, days=None):
    """
    从数据库获取媒体URL列表
    
    Args:
        status: 媒体的下载状态 ('pending', 'failed', 'success', 'skipped')
        limit: 最大返回数量
        days: 只返回最近几天的媒体
        
    Returns:
        符合条件的媒体记录列表
    """
    logger.info(f"正在获取状态为 '{status}' 的媒体URL列表")
    
    try:
        if status == 'pending':
            # 使用find_pending方法
            media_list = youran.db.media_urls.find_pending(limit=limit, days=days)
        else:
            # 使用find_by_status方法
            media_list = youran.db.media_urls.find_by_status(status, limit=limit)
            
        logger.info(f"成功获取 {len(media_list)} 条媒体记录")
        return media_list
    except Exception as e:
        logger.error(f"获取媒体URL列表时出错: {repr(e)}")
        return []

def download_media(media, use_proxy=True, max_retries=1):
    """
    下载单个媒体文件
    
    Args:
        media: 媒体记录
        use_proxy: 是否使用代理
        max_retries: 最大重试次数
        
    Returns:
        (success, file_content) 元组
    """
    media_id = media['_id']
    media_url = media['media_url']
    media_type = media['media_type']
    
    logger.info(f"开始下载 {media_id}: {media_url}")
    
    # 设置适当的请求头
    if media_type == 'image':
        headers = youran.headers.img
        media_url=media_url[0]
    elif media_type == 'video':
        headers = youran.headers.video
        if 'oasis.video.weibocdn.com' in media_url:
            headers = youran.headers.mobile
    else:
        headers = youran.headers.mobile
    
    # 下载文件
    retries = 0
    while retries <= max_retries:
        try:
            # 使用youran的下载方法
            content = None
            if media_type == 'image':
                content = youran.net.img.download(media_url,proxy=True, progress=True, headers=headers)
            elif media_type == 'video':
                file_name = youran.net.video._extract_video_name(media_url)
                if file_name in media_url:
                    content = youran.net.BaseNet.download(media_url, progress=True, headers=youran.headers.video)
                else:
                    import urllib
                    redirected_url = urllib.request.urlopen(media_url).geturl()
                    content = youran.net.BaseNet.download(redirected_url, progress=True, headers=youran.headers.video, proxy=use_proxy)
            else:
                content = youran.net.BaseNet.download(media_url, progress=True, headers=headers, proxy=use_proxy)
            
            if content and len(content) > 0:
                logger.info(f"下载成功: {media_id}")
                return True, content
            else:
                logger.warning(f"下载内容为空: {media_id}")
        except Exception as e:
            logger.error(f"下载出错: {repr(e)}")
        
        # 重试
        retries += 1
        if retries <= max_retries:
            delay = random.randint(1, 5)
            logger.info(f"等待 {delay} 秒后重试 ({retries}/{max_retries})...")
            time.sleep(delay)
    
    logger.error(f"下载失败，已达到最大重试次数: {media_id}")
    return False, None

def save_to_minio(media, content):
    """
    将媒体内容保存到MinIO
    
    Args:
        media: 媒体记录
        content: 文件内容
        
    Returns:
        成功返回True，失败返回False
    """
    try:
        media_id = media['_id']
        media_type = media['media_type']
        media_url = media['media_url']
        
        # 根据媒体类型确定存储路径和文件名
        if media_type == 'image':
            storage_type = 'imgs'
            file_name = media_url[0].split('/')[-1]
        else:
            storage_type = 'videos'
            file_name = youran.net.video._extract_video_name(media_url)

        path = f"{storage_type}/{file_name}"
        logger.info(f"解析到媒体名字为: {file_name}")
        # 保存到MinIO
        min.save_weibo(path, content)
        logger.info(f"已上传到MinIO: {path}")
        return True
    except Exception as e:
        logger.error(f"保存到MinIO出错: {repr(e)}")
        return False

def update_status(media_id, status):
    """
    更新媒体下载状态
    
    Args:
        media_id: 媒体ID
        status: 新状态 ('success', 'failed', 'skipped')
        
    Returns:
        成功返回True，失败返回False
    """
    try:
        return youran.db.media_urls.update_status(media_id, status)
    except Exception as e:
        logger.error(f"更新状态出错: {repr(e)}")
        return False

def download_all_media(limit=None, days=None, status='pending', use_proxy=True, max_retries=1):
    """
    下载所有符合条件的媒体
    
    Args:
        limit: 最大处理数量
        days: 只处理最近几天的媒体
        status: 媒体状态
        use_proxy: 是否使用代理
        max_retries: 最大重试次数
        
    Returns:
        (成功数量, 失败数量, 跳过数量) 元组
    """
    # 1. 从media_urls表中获取媒体列表
    media_list = get_media_urls(status, limit, days)
    
    if not media_list:
        logger.info("没有找到符合条件的媒体，任务结束")
        return 0, 0, 0
    
    success_count = 0
    failed_count = 0
    skipped_count = 0
    total_count = len(media_list)
    
    logger.info(f"开始下载 {total_count} 个媒体文件")
    
    # 2. 依次下载媒体
    for i, media in enumerate(media_list):
        media_id = media['_id']
        if media["media_type"] == 'video':
            logger.warning('跳过视频')
            update_status(media_id, 'success')
            continue
    
        retry_count = media.get('retry_count', 0)
        
        # 显示进度
        progress = f"[{i+1}/{total_count}] ({(i+1)/total_count*100:.1f}%)"
        logger.info(f"{progress} 处理: {media_id}")
        
        # 检查重试次数是否超出限制
        if retry_count >= max_retries:
            logger.warning(f"{progress} 跳过已达到最大重试次数的媒体: {media_id}")
            update_status(media_id, 'skipped')
            skipped_count += 1
            continue
        
        # 下载媒体文件
        success, content = download_media(media, use_proxy, max_retries)
        
        if success and content:
            # 保存到MinIO
            if save_to_minio(media, content):
                # 更新状态
                update_status(media_id, 'success')
                success_count += 1
            else:
                # 更新状态为失败
                update_status(media_id, 'failed')
                failed_count += 1
        else:
            # 更新状态为失败
            update_status(media_id, 'failed')
            failed_count += 1
        
        # 随机延时，避免被反爬
        if i < total_count - 1:  # 不是最后一个
            delay = random.uniform(0.5, 2.0)
            time.sleep(delay)
    
    logger.info(f"下载任务完成。总计: {total_count}, 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}")
    return success_count, failed_count, skipped_count

def display_stats():
    """显示媒体URL统计信息"""
    try:
        # 获取基本统计信息
        stats = youran.db.media_urls.get_stats()
        
        logger.info("====== 媒体URL统计信息 ======")
        logger.info(f"总计: {stats['total']} 个媒体URL")
        logger.info(f"待下载: {stats['pending']} ({stats['pending']/stats['total']*100:.1f}%)")
        logger.info(f"已下载: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        logger.info(f"下载失败: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
        logger.info(f"已跳过: {stats['skipped']} ({stats['skipped']/stats['total']*100:.1f}%)")
        
        # 获取媒体类型统计
        type_stats = youran.db.media_urls.get_media_types_count()
        logger.info("\n媒体类型分布:")
        for media_type, count in type_stats.items():
            logger.info(f"- {media_type}: {count} ({count/stats['total']*100:.1f}%)")
        
        # 获取最近添加的媒体
        recent = youran.db.media_urls.find_recently_added(days=1, limit=1)
        if recent:
            recent_time = datetime.fromtimestamp(recent[0].get('add_time', 0))
            logger.info(f"\n最近添加: {recent_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        logger.error(f"获取统计信息时出错: {repr(e)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="从数据库获取媒体URL并下载")
    parser.add_argument("--status", choices=["pending", "failed", "success", "skipped"], default="pending", 
                        help="要处理的媒体状态")
    parser.add_argument("--limit", type=int, default=500,
                        help="最大处理数量")
    parser.add_argument("--days", type=int, default=500, 
                        help="只处理最近N天的媒体")
    parser.add_argument("--no-proxy", action="store_true", 
                        help="不使用代理")
    parser.add_argument("--retries", type=int, default=1, 
                        help="下载失败时的最大重试次数")
    parser.add_argument("--stats", action="store_true", 
                        help="仅显示统计信息，不执行下载")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", 
                        help="日志级别")
    parser.add_argument("--log-file", default="media_downloader.log", 
                        help="日志文件名")
    
    args = parser.parse_args()
    
    # 设置日志级别
    log_level = getattr(logging, args.log_level)
    global logger
    logger = setup_logger(log_file=args.log_file, level=log_level)
    
    logger.info(f"=== 开始运行简化版 Media Downloader ===")
    logger.info(f"当前设置: 状态={args.status}, 限制={args.limit}, 最近天数={args.days}, 使用代理={not args.no_proxy}")
    
    try:
        # 仅显示统计信息
        if args.stats:
            display_stats()
            return
            
        # 开始下载
        start_time = time.time()
        success_count, failed_count, skipped_count = download_all_media(
            limit=args.limit,
            days=args.days,
            status=args.status,
            use_proxy=not args.no_proxy,
            max_retries=args.retries
        )
        
        # 显示结果
        elapsed_time = time.time() - start_time
        logger.info(f"下载完成，耗时: {elapsed_time:.1f}秒")
        logger.info(f"总计处理: {success_count + failed_count + skipped_count} 个媒体")
        logger.info(f"成功下载: {success_count}，下载失败: {failed_count}，已跳过: {skipped_count}")
        
        # 显示统计信息
        display_stats()
        
    except KeyboardInterrupt:
        logger.warning("用户中断下载")
    except Exception as e:
        logger.error(f"下载过程中发生错误: {repr(e)}", exc_info=True)
    finally:
        logger.info("=== 下载器运行结束 ===")

if __name__ == "__main__":
    # 示例用法:
    # 下载10个待处理的媒体:
    # python download_media.py --limit 10
    
    # 下载最近3天添加的待处理媒体:
    # python download_media.py --days 3
    
    # 重试下载失败的媒体:
    # python download_media.py --status failed
    
    # 仅显示统计信息:
    # python download_media.py --stats
    while True:
        main()
        time.sleep(10*60)