"""
认证模块 (Authentication Module)

该模块处理用户认证相关功能，包括：
- 用户登录和验证
- 用户注销
- 用户注册
- 登录状态检查和保护路由

该模块使用 Flask Blueprint 实现，包含认证相关的路由和功能。
"""

import functools
import logging
from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import BadRequest

from flaskr.db import get_db
from flaskr import dbutils

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """视图装饰器，将未登录用户重定向到登录页面。
    
    Args:
        view: 需要保护的视图函数
        
    Returns:
        装饰后的视图函数，确保只有登录用户可以访问
    """
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        logger.info('='*40 + ' 登录检测 ' + '='*40)
        
        if session.get("uid") is None:
            logger.info('用户未登录，重定向到登录页面')
            return redirect(url_for("auth.login"))
            
        logger.info('用户已登录，通过验证')
        return view(**kwargs)
    
    return wrapped_view


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """处理用户登录请求。
    
    GET: 显示登录表单
    POST: 处理登录表单提交，验证用户凭据
    
    Returns:
        成功登录后重定向到主页，否则显示登录页面
    """
    logger.info('='*40 + ' 登录请求 ' + '='*40)
    
    # 准备热门内容数据，用于登录页面显示
    hot_items = dbutils.get_hot()
    
    # 处理表单提交
    if request.method == 'POST':
        try:
            form_data = dict(request.form)
            logger.info(f'接收到的登录表单数据: {form_data}')
            
            uname = request.form.get('uname', '')
            psw = request.form.get('psw', '')
            
            # 输入验证
            error = None
            if not uname:
                error = "用户名不能为空"
            elif not psw:
                error = "密码不能为空"
                
            if error:
                flash(error)
                return render_template('auth/login.html', dicts={'items': hot_items})
                
            # 验证用户凭据
            user = get_db().account.find_user(uname)
            
            if user and user[0]['uname'] == uname and user[0]['psw'] == psw:
                # 登录成功
                session.clear()
                session['uid'] = user[0]['_id']
                logger.info(f'用户 {uname} (ID: {session["uid"]}) 登录成功')
                
                # 重定向到主页
                return redirect(url_for('blog.index'))
            else:
                # 登录失败
                logger.warning(f'用户 {uname} 登录失败：无效的用户名或密码')
                flash('无效的用户名或密码')
        except Exception as e:
            logger.error(f'登录过程中发生错误: {str(e)}')
            flash('登录过程中发生错误，请稍后再试')
    
    # GET 请求或登录失败，显示登录页面
    return render_template('auth/login.html', dicts={'items': hot_items})


@bp.route('/logout', methods=['GET'])
def logout():
    """处理用户注销请求。
    
    清除会话并重定向到登录页面。
    
    Returns:
        重定向到登录页面
    """
    logger.info('='*40 + ' 注销请求 ' + '='*40)
    
    # 记录谁注销了
    user_id = session.get('uid')
    if user_id:
        logger.info(f'用户 ID: {user_id} 已注销')
    
    # 清除会话
    session.clear()
    
    # 重定向到登录页面
    return redirect(url_for('auth.login'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """处理用户注册请求。
    
    GET: 显示注册表单
    POST: 处理注册表单提交，创建新用户
    
    Returns:
        成功注册后重定向到主页，否则显示注册页面
    """
    logger.info('='*40 + ' 注册请求 ' + '='*40)
    
    # 准备热门内容数据，用于注册页面显示
    hot_items = dbutils.get_hot()
    
    # 处理表单提交
    if request.method == 'POST':
        try:
            form_data = dict(request.form)
            logger.info(f'接收到的注册表单数据: {form_data}')
            
            uid = request.form.get('uid', '')
            uname = request.form.get('uname', '')
            psw = request.form.get('psw', '')
            
            # 输入验证
            error = None
            if not uid:
                error = "用户ID不能为空"
            elif not uname:
                error = "用户名不能为空"
            elif not psw:
                error = "密码不能为空"
            elif len(psw) < 3:
                error = "密码长度不能少于3个字符"
                
            if error:
                flash(error)
                return render_template('auth/register.html', dicts={'items': hot_items}, error=error)
            
            # 检查用户ID是否已存在
            existing_user = get_db().user.find_users([uid])
            if existing_user and existing_user.count():
                logger.warning(f'注册失败：用户ID {uid} 已存在')
                return render_template('auth/register.html', dicts={'items': hot_items}, error='用户ID已被使用')
            
            # 创建新用户
            # 注意：此处应考虑对密码进行哈希处理以提高安全性
            # psw_hash = generate_password_hash(psw)
            new_user = {
                '_id': uid,
                'uname': uname,
                'psw': psw  # 在实际生产环境中应使用 psw_hash
            }
            
            get_db().account.add(new_user)
            logger.info(f'用户 {uname} (ID: {uid}) 注册成功')
            
            # 自动登录
            session.clear()
            session['uid'] = uid
            
            # 重定向到主页
            return redirect(url_for('blog.index'))
            
        except Exception as e:
            logger.error(f'注册过程中发生错误: {str(e)}')
            flash('注册过程中发生错误，请稍后再试')
    
    # GET 请求或注册失败，显示注册页面
    return render_template('auth/register.html', dicts={'items': hot_items})


@bp.before_app_request
def load_logged_in_user():
    """在处理请求前加载已登录用户信息。
    
    如果用户已登录，将用户信息存储在 g.user 中，
    便于在请求处理过程中访问。
    """
    user_id = session.get('uid')
    
    if user_id is None:
        g.user = None
    else:
        # 从数据库加载用户信息
        try:
            g.user = get_db().account.find_user(user_id)
        except Exception as e:
            logger.error(f'加载用户信息时出错: {str(e)}')
            g.user = None
