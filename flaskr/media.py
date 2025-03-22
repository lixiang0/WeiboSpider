"""
媒体模块 (Media Module)

该模块处理媒体相关功能，包括：
- 微博媒体文件的下载和展示
- B站视频下载统计和处理
- 用户留言功能实现
- 文件展示页面

该模块使用 Flask Blueprint 实现，包含媒体相关的路由和功能。
"""

import io
import time
from datetime import datetime
import logging
from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, session, url_for, send_file, abort, current_app
)
from flask_cors import cross_origin
from werkzeug.exceptions import abort, BadRequest
from werkzeug.utils import secure_filename

from flaskr import db, dbutils
from flaskr.auth import login_required
from flaskr.db import get_media

import youran

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint("media", __name__)


@bp.route('/static/<ttype>/<name>')
def download_file(ttype, name):
    """处理微博媒体文件下载请求。
    
    根据类型和文件名从存储中获取媒体文件，如图片、视频等。
    
    Args:
        ttype: 媒体类型 (img, video等)
        name: 文件名
        
    Returns:
        媒体文件的响应
    """
    logger.info('='*40 + ' 媒体文件下载 ' + '='*40)
    logger.info(f'请求下载 - 类型: {ttype}, 文件名: {name}')
    
    # 安全检查
    secured_name = secure_filename(name)
    if secured_name != name:
        logger.warning(f'可疑的文件名请求: {name}')
        abort(400, description="Invalid filename")
    
    try:
        # 获取媒体内容
        media_data = get_media().get_weibo_media(ttype, secured_name)
        if not media_data:
            logger.error(f'文件未找到 - 类型: {ttype}, 文件名: {secured_name}')
            abort(404, description="File not found")
        
        # 根据文件类型设置合适的MIME类型
        mime_type = 'image/jpeg'  # 默认MIME类型
        if secured_name.lower().endswith(('.mp4', '.avi', '.mov')):
            mime_type = 'video/mp4'
        elif secured_name.lower().endswith('.gif'):
            mime_type = 'image/gif'
        elif secured_name.lower().endswith('.png'):
            mime_type = 'image/png'
        
        logger.info(f'成功获取媒体文件 - 类型: {ttype}, 文件名: {secured_name}, MIME类型: {mime_type}')
        
        # 从内存字节返回文件
        return send_file(
            io.BytesIO(media_data),
            mimetype=mime_type,
            as_attachment=True,
            download_name=secured_name
        )
    except Exception as e:
        logger.error(f'下载文件 {secured_name} 时出错: {str(e)}')
        flash('文件下载失败，请稍后再试')
        abort(500, description="File download failed")


@bp.route('/download/<name>')
def download_bilibili(name):
    """处理B站视频下载请求。
    
    记录下载统计并提供视频文件。
    
    Args:
        name: 视频文件名
        
    Returns:
        视频文件的响应
    """
    logger.info('='*40 + ' B站视频下载 ' + '='*40)
    logger.info(f'请求下载B站视频: {name}')
    
    # 安全检查
    secured_name = secure_filename(name)
    if secured_name != name:
        logger.warning(f'可疑的B站视频文件名请求: {name}')
        abort(400, description="Invalid filename")
    
    try:
        # 准备记录ID (去除文件扩展名)
        file_id = secured_name.rsplit('.', 1)[0] if '.' in secured_name else secured_name
        record_data = {'_id': file_id, 'filename': file_id}
        
        # 查询现有记录
        logger.info(f'处理下载记录: {record_data}')
        existing_records = list(dbutils.find_count(record_data))
        record_count = len(existing_records)
        logger.info(f'找到 {record_count} 条记录')
        
        # 更新或创建下载计数记录
        record = existing_records[0] if record_count > 0 else {'count': 0, '_id': file_id, 'filename': file_id}
        record['count'] = record.get('count', 0) + 1
        record['last_download'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 保存记录
        dbutils.add_count(record)
        logger.info(f'更新记录: {record}')
        
        # 返回文件
        logger.info(f'提供文件下载: static/{secured_name}')
        return send_file(f'static/{secured_name}', as_attachment=True)
    except FileNotFoundError:
        logger.error(f'B站视频文件未找到: {secured_name}')
        flash('请求的文件不存在')
        abort(404, description="File not found")
    except Exception as e:
        logger.error(f'处理B站视频 {secured_name} 下载时出错: {str(e)}')
        flash('文件下载失败，请稍后再试')
        abort(500, description="File download failed")


@bp.route('/files/<name>', methods=['GET'])
@bp.route('/files', methods=['GET', 'POST'])
def index(name=None):
    """文件列表和留言处理页面。
    
    处理留言提交和展示文件列表。
    如果提供name参数，显示特定的模板页面；
    否则显示默认文件列表页面。
    
    Args:
        name: 可选的特定页面名称
        
    Returns:
        文件列表页面或特定模板页面
    """
    logger.info('='*40 + ' 文件列表/留言页面 ' + '='*40)
    
    # POST请求处理留言提交
    if request.method == 'POST':
        logger.info('处理留言提交')
        
        try:
            # 获取表单数据
            uname = request.form.get('uname', '').strip()
            utext = request.form.get('utext', '').strip()
            
            # 输入验证
            if not uname:
                logger.warning('留言用户名为空')
                flash('请输入您的用户名')
                return render_template('files/index.html', dicts={'liuyan': True, 'error': '用户名不能为空'})
            
            if not utext:
                logger.warning('留言内容为空')
                flash('请输入留言内容')
                return render_template('files/index.html', dicts={'liuyan': True, 'error': '留言内容不能为空'})
            
            # 防止频繁提交 (限制为10分钟)
            last_post = session.get(f'liuyan_{uname}', 0)
            cooldown_period = 10 * 60  # 10分钟冷却时间
            
            if time.time() - last_post < cooldown_period:
                logger.warning(f'用户 {uname} 提交过于频繁，距离上次提交: {int(time.time() - last_post)} 秒')
                remaining_time = int(cooldown_period - (time.time() - last_post)) // 60
                flash(f'您的留言提交过于频繁，请等待 {remaining_time} 分钟后再试')
                return render_template('error.html', dicts={'error': '提交频率限制', 'message': f'请等待 {remaining_time} 分钟后再试'})
            
            # 更新提交时间
            session[f'liuyan_{uname}'] = time.time()
            
            # 获取当前留言数量作为ID
            count = len(list(dbutils.find_liuyan()))
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 创建留言记录
            new_message = {
                '_id': count,
                'uname': uname,
                'utext': utext,
                'create_at': current_time,
                'ip': request.remote_addr  # 可选：记录IP地址
            }
            
            # 保存留言
            dbutils.add_liuyan(new_message)
            logger.info(f'留言已保存 - 用户: {uname}, ID: {count}')
            
            # 准备模板数据
            para = {
                'liuyan': True,
                'items': list(dbutils.find_liuyan()),
                'success': '留言提交成功！'
            }
            
            flash('您的留言已成功提交！')
            return render_template('files/index.html', dicts=para)
            
        except Exception as e:
            logger.error(f'处理留言提交时出错: {str(e)}')
            flash('留言提交失败，请稍后再试')
            return render_template('files/index.html', dicts={'liuyan': True, 'error': '系统错误，请稍后再试'})
    
    # GET请求处理文件列表展示
    try:
        # 获取留言列表
        items = dbutils.find_liuyan()
        
        # 如果提供了特定页面名称
        if name:
            logger.info(f'请求特定页面: {name}')
            
            # 定义可用的模板映射
            templates = {
                'bili1': 'files/bili1.html',
                'bili2': 'files/bili2.html',
                'bili3': 'files/bili3.html'
            }
            
            # 验证请求的页面是否有效
            if name not in templates:
                logger.warning(f'请求的页面无效: {name}')
                abort(404, description="Page not found")
            
            # 获取下载计数
            record_data = {'_id': name}
            count_records = list(dbutils.find_count(record_data))
            download_count = count_records[0]['count'] if count_records else 0
            
            logger.info(f'页面 {name} 的下载计数: {download_count}')
            
            # 准备模板数据
            para = {
                'liuyan': False,
                'items': list(items),
                'count': download_count
            }
            
            # 渲染特定模板
            return render_template(templates[name], dicts=para)
        
        # 默认文件列表页面
        else:
            logger.info('请求默认文件列表页面')
            
            # 准备模板数据
            para = {
                'liuyan': False,
                'items': list(items)
            }
            
            # 渲染默认模板
            return render_template('files/index.html', dicts=para)
            
    except Exception as e:
        logger.error(f'展示文件列表时出错: {str(e)}')
        flash('加载页面失败，请稍后再试')
        abort(500, description="Error loading page")


@bp.errorhandler(404)
def page_not_found(e):
    """处理404错误。
    
    Returns:
        错误页面
    """
    logger.warning(f'404错误: {request.path}')
    return render_template('error.html', dicts={'error': '404 - 页面未找到', 'message': '您请求的页面不存在'}), 404


@bp.errorhandler(500)
def server_error(e):
    """处理500错误。
    
    Returns:
        错误页面
    """
    logger.error(f'500错误: {str(e)}')
    return render_template('error.html', dicts={'error': '500 - 服务器错误', 'message': '服务器处理请求时出错，请稍后再试'}), 500