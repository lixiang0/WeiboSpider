"""
博客模块 (Blog Module)

该模块处理博客相关功能，包括：
- 首页和用户主页显示
- 博客列表和详情展示
- 收藏和关注功能
- 搜索和热门内容
- 评论和意见反馈

该模块使用 Flask Blueprint 实现，包含博客相关的路由和功能。
"""

import logging
from flask import (
    Blueprint, flash, g, redirect, render_template,
    request, session, url_for, abort, current_app
)
from flask_cors import cross_origin
from werkzeug.exceptions import abort, BadRequest

from flaskr.auth import login_required
from flaskr import dbutils

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建蓝图
bp = Blueprint("blog", __name__)


@bp.route('/')
def index():
    """网站首页视图。
    
    未登录用户显示登录页面，已登录用户重定向到用户主页。
    
    Returns:
        登录页面或重定向到用户主页
    """
    logger.info('='*40 + ' 访问首页 ' + '='*40)
    
    if 'uid' in session:
        logger.info(f'用户 {session["uid"]} 已登录，重定向到用户主页')
        return redirect(url_for('blog.uindex'))
    
    # 准备首页数据
    para = {
        'items': dbutils.get_hot(),
        'users': dbutils.random_user(10),
    }
    
    logger.info('未登录用户，显示登录页面')
    return render_template('auth/login.html', dicts=para)


@bp.route('/u/<uid>')
@bp.route('/u')
@cross_origin()
@login_required
def uindex(uid=None):
    """用户主页视图，显示用户信息和微博动态。
    
    如果提供uid参数，显示指定用户主页；
    否则显示当前登录用户的主页。
    
    Args:
        uid: 可选的用户ID
        
    Returns:
        用户主页视图
    """
    logger.info('='*40 + ' 访问用户主页 ' + '='*40)
    
    # 获取页码，确保有效
    try:
        pagenum = max(0, int(request.args.get('page', 0)))
    except ValueError:
        pagenum = 0
    
    logger.info(f'用户ID: {uid or "当前登录用户"}, 页码: {pagenum}')
    
    userinfo = None
    blogs = []
    follow_list = []
    follow_status = False
    
    current_user_id = int(session['uid'])
    
    # 处理用户主页逻辑
    if uid:
        # 访问指定用户主页
        logger.info(f'显示用户 {uid} 的主页')
        userinfo = dbutils.get_user(uid=uid)
        follow_list = [int(uid)]
        
        # 检查当前用户是否关注了该用户
        user_follows = [int(u['blogger']) for u in list(dbutils.get_follows(current_user_id))]
        follow_status = int(uid) in user_follows
        logger.info(f'关注状态: {"已关注" if follow_status else "未关注"}')
    else:
        # 访问当前用户主页
        logger.info(f'显示当前登录用户 {current_user_id} 的主页')
        follow_list = [u['blogger'] for u in dbutils.get_follows(current_user_id)]
        logger.info(f'关注用户列表: {follow_list}')
    
    # 获取微博数据
    try:
        blog_data = dbutils.get_page(follow_list, pagenum)
        
        # 处理每条微博数据
        for data in blog_data:
            _, video_name = dbutils.net.video.extract(data)
            if video_name is not None:
                data['video_name'] = video_name
            
            # 处理转发微博
            if 'retweeted_status' in data:
                data['retweeted_status']['video_name'] = video_name
            
            blogs.append(data)
    except Exception as e:
        logger.error(f'获取微博数据时出错: {str(e)}')
        flash('获取数据时出错，请刷新页面重试')
    
    # 准备模板数据
    para = {
        'follow': follow_status,
        'blogs': list(blogs),
        'curr': pagenum,
        'user': userinfo,
        'items': dbutils.get_hot(),
        'users': dbutils.random_user(10),
    }
    
    return render_template('base.html', dicts=para)


@bp.route('/f/<uid>')
@bp.route('/f')
@login_required
@cross_origin()
def get_follows(uid=None):
    """获取用户关注列表。
    
    显示当前登录用户关注的所有用户列表。
    
    Args:
        uid: 可选的用户ID，当前未使用
        
    Returns:
        关注列表页面
    """
    logger.info('='*40 + ' 获取关注列表 ' + '='*40)
    
    # 使用当前登录用户ID
    current_user_id = int(session['uid'])
    logger.info(f'当前用户: {current_user_id}')
    
    try:
        # 获取关注列表
        follows = [int(u['blogger']) for u in list(dbutils.get_follows(current_user_id))]
        logger.info(f'关注用户ID列表: {follows}')
        
        # 获取用户详细信息
        users = dbutils.get_users(list(follows))
        logger.info(f'获取到 {len(users)} 个关注用户信息')
        
        # 准备模板数据
        para = {
            'follow': True,
            'users1': users,
            'items': dbutils.get_hot(),
            'users': dbutils.random_user(10),
        }
        
        return render_template('blog/follows.html', dicts=para)
    except Exception as e:
        logger.error(f'获取关注列表时出错: {str(e)}')
        flash('获取关注列表时出错，请刷新页面重试')
        return render_template('blog/follows.html', dicts={'error': '获取数据出错'})


@bp.route('/r/blog/<num>')
@cross_origin()
def get_random_20(num):
    """获取随机微博列表。
    
    Args:
        num: 要获取的随机微博数量
        
    Returns:
        包含随机微博的页面
    """
    logger.info('='*40 + ' 获取随机微博 ' + '='*40)
    
    try:
        num = int(num)
        num = min(50, max(1, num))  # 限制范围 1-50
        logger.info(f'请求 {num} 条随机微博')
        
        # 获取随机微博
        blogs = dbutils.random_blog(num)
        
        # 准备模板数据
        para = {
            'blogs': list(blogs),
            'curr': 0,
            'items': dbutils.get_hot(),
        }
        
        return render_template('base.html', dicts=para)
    except ValueError:
        logger.error(f'获取随机微博时参数错误: {num}')
        abort(400, description="Invalid number parameter")
    except Exception as e:
        logger.error(f'获取随机微博时出错: {str(e)}')
        flash('获取随机微博时出错，请刷新页面重试')
        return render_template('base.html', dicts={'error': '获取数据出错'})


@bp.route('/r/f/<num>')
@cross_origin()
def get_random_follows(num):
    """获取随机用户列表。
    
    Args:
        num: 要获取的随机用户数量
        
    Returns:
        包含随机用户的页面
    """
    logger.info('='*40 + ' 获取随机用户 ' + '='*40)
    
    try:
        num = int(num)
        num = min(50, max(1, num))  # 限制范围 1-50
        logger.info(f'请求 {num} 个随机用户')
        
        # 获取随机用户
        users = dbutils.random_user(num)
        
        # 准备模板数据
        para = {
            'users': users,
        }
        
        return render_template('blog/follows.html', dicts=para)
    except ValueError:
        logger.error(f'获取随机用户时参数错误: {num}')
        abort(400, description="Invalid number parameter")
    except Exception as e:
        logger.error(f'获取随机用户时出错: {str(e)}')
        flash('获取随机用户时出错，请刷新页面重试')
        return render_template('blog/follows.html', dicts={'error': '获取数据出错'})


@bp.route('/about')
def about():
    """关于页面，显示系统统计信息。
    
    Returns:
        关于页面
    """
    logger.info('='*40 + ' 访问关于页面 ' + '='*40)
    
    try:
        # 获取统计数据
        count = dbutils.db.mblog.counts({})
        authors = dbutils.db.user.counts({})
        states = dbutils.db.states.find({})
        
        # 获取用户数量和微博数量历史数据
        user_count = [item['count'] for item in dbutils.db.states.find({"name": "user_count"})]
        mblog_count = [item['count'] for item in dbutils.db.states.find({"name": "mblog_count"})]
        dates = [int(item['update_time']) for item in dbutils.db.states.find({"name": "mblog_count"})]
        
        # 准备模板数据
        para = {
            'count': count,
            'authors': authors,
            'user': None,
            'items': dbutils.get_hot(),
            'users': dbutils.random_user(10),
            'states': dbutils.db.states.find({}),
            "dates": dates,
            "user_count": user_count,
            "mblog_count": mblog_count,
        }
        
        return render_template('about.html', dicts=para)
    except Exception as e:
        logger.error(f'获取关于页面数据时出错: {str(e)}')
        flash('加载统计数据时出错，请刷新页面重试')
        return render_template('about.html', dicts={'error': '获取数据出错'})


@bp.route('/hot/<url>')
def hot(url):
    """显示热门话题页面。
    
    Args:
        url: 热门话题URL参数
        
    Returns:
        热门话题页面
    """
    logger.info('='*40 + ' 访问热门话题 ' + '='*40)
    logger.info(f'热门话题URL: {url}')
    
    try:
        mblogs = []
        count = dbutils.db.mblog.counts({})
        authors = dbutils.db.user.counts({})
        
        # 构建完整URL
        full_url = f'https://weibo.com/a/hot/{url}'
        logger.info(f'完整URL: {full_url}')
        
        # 获取热门微博IDs
        bids = dbutils.get_hot_bids(full_url)
        logger.info(f'获取到 {len(bids)} 个热门微博ID')
        
        # 获取微博详情
        for bid in bids:
            mblog = dbutils.get_mblog_bid(bid)
            if mblog:
                # 处理视频链接
                _, video_name = dbutils.net.video.extract(mblog)
                if video_name is not None:
                    mblog['video_name'] = video_name
                
                # 处理转发微博
                if 'retweeted_status' in mblog:
                    mblog['retweeted_status']['video_name'] = video_name
                
                mblogs.append(mblog)
        
        # 准备模板数据
        para = {
            'blogs': list(mblogs),
            'count': count,
            'authors': authors,
            'curr': 1,
            'items': dbutils.get_hot(),
            'users': dbutils.random_user(10),
        }
        
        return render_template('base.html', dicts=para)
    except Exception as e:
        logger.error(f'获取热门话题数据时出错: {str(e)}')
        flash('获取热门话题数据时出错，请刷新页面重试')
        return render_template('base.html', dicts={'error': '获取数据出错'})


@bp.route('/b/<bid>')
def blog(bid):
    """显示单条微博的详情页面。
    
    Args:
        bid: 微博ID
        
    Returns:
        微博详情页面
    """
    logger.info('='*40 + ' 访问微博详情 ' + '='*40)
    logger.info(f'微博ID: {bid}')
    
    try:
        # 获取微博详情
        mblog = dbutils.get_mblog_bid(bid)
        if not mblog:
            logger.warning(f'微博 {bid} 不存在')
            abort(404, description="Blog not found")
        
        # 处理视频链接
        _, video_name = dbutils.net.video.extract(mblog)
        if video_name is not None:
            mblog['video_name'] = video_name
        
        # 处理转发微博
        if 'retweeted_status' in mblog:
            mblog['retweeted_status']['video_name'] = video_name
        
        # 获取评论
        comments = dbutils.get_comment(mblog['_id'])
        logger.info(f'获取到 {len(comments) if comments else 0} 条评论')
        
        # 准备模板数据
        para = {
            'blogs': [mblog],
            'comments': comments,
            'items': dbutils.get_hot(),
            'users': dbutils.random_user(10),
        }
        
        return render_template('blog/index.html', dicts=para)
    except Exception as e:
        logger.error(f'获取微博详情时出错: {str(e)}')
        flash('获取微博详情时出错，请刷新页面重试')
        return render_template('blog/index.html', dicts={'error': '获取数据出错'})


@bp.route('/fav/<bid>')
@bp.route('/fav')
@login_required
def fav(bid=None):
    """收藏微博或显示收藏列表。
    
    如果提供bid参数，执行收藏操作；
    否则显示当前用户的收藏列表。
    
    Args:
        bid: 可选的微博ID
        
    Returns:
        成功消息或收藏列表页面
    """
    logger.info('='*40 + ' 收藏操作 ' + '='*40)
    
    current_user_id = session['uid']
    logger.info(f'当前用户: {current_user_id}')
    
    # 收藏指定微博
    if bid:
        logger.info(f'收藏微博: {bid}')
        
        try:
            # 检查是否已收藏
            if dbutils.is_fav(current_user_id, bid):
                logger.warning(f'微博 {bid} 已经被收藏')
                return '该微博已收藏'
            
            # 添加收藏
            dbutils.add_fav(current_user_id, bid)
            logger.info(f'成功收藏微博 {bid}')
            return '收藏成功'
        except Exception as e:
            logger.error(f'收藏微博 {bid} 时出错: {str(e)}')
            return '收藏失败，请稍后再试'
    
    # 显示收藏列表
    try:
        # 获取收藏的微博ID列表
        bids = [item['bid'] for item in dbutils.get_fav(current_user_id)]
        logger.info(f'获取到 {len(bids)} 个收藏微博ID')
        
        # 获取微博详情
        mblogs = dbutils.get_mblog_bids(bids)
        
        # 准备模板数据
        para = {
            'blogs': list(mblogs),
            'fav': True,
            'curr': 1,
            'items': dbutils.get_hot(),
            'users': dbutils.random_user(10),
        }
        
        return render_template('base.html', dicts=para)
    except Exception as e:
        logger.error(f'获取收藏列表时出错: {str(e)}')
        flash('获取收藏列表时出错，请刷新页面重试')
        return render_template('base.html', dicts={'error': '获取数据出错'})


@bp.route('/follow/<fuid>')
@login_required
def follow(fuid):
    """关注用户。
    
    Args:
        fuid: 要关注的用户ID
        
    Returns:
        重定向到关注列表页面
    """
    logger.info('='*40 + ' 关注用户 ' + '='*40)
    
    current_user_id = session['uid']
    logger.info(f'当前用户 {current_user_id} 尝试关注用户 {fuid}')
    
    try:
        # 检查是否已关注
        if dbutils.is_follow(current_user_id, fuid):
            logger.warning(f'用户 {fuid} 已被关注')
            flash('您已关注该用户')
            return redirect(url_for('blog.get_follows'))
        
        # 添加关注
        if not dbutils.add_follow(current_user_id, fuid):
            logger.error(f'关注用户 {fuid} 失败')
            flash('关注失败，请稍后再试')
        else:
            logger.info(f'成功关注用户 {fuid}')
            flash('关注成功')
        
        return redirect(url_for('blog.get_follows'))
    except Exception as e:
        logger.error(f'关注用户 {fuid} 时出错: {str(e)}')
        flash('关注操作失败，请稍后再试')
        return redirect(url_for('blog.get_follows'))


@bp.route('/ufav/<fbid>')
@login_required
def ufav(fbid):
    """取消收藏微博。
    
    Args:
        fbid: 要取消收藏的微博ID
        
    Returns:
        重定向到收藏列表页面
    """
    logger.info('='*40 + ' 取消收藏 ' + '='*40)
    
    current_user_id = session['uid']
    logger.info(f'当前用户 {current_user_id} 取消收藏微博 {fbid}')
    
    try:
        dbutils.del_fav(current_user_id, fbid)
        logger.info(f'成功取消收藏微博 {fbid}')
        flash('已取消收藏')
    except Exception as e:
        logger.error(f'取消收藏微博 {fbid} 时出错: {str(e)}')
        flash('取消收藏失败，请稍后再试')
    
    return redirect(url_for('blog.fav'))


@bp.route('/ufollow/<fuid>')
@login_required
def ufollow(fuid):
    """取消关注用户。
    
    Args:
        fuid: 要取消关注的用户ID
        
    Returns:
        重定向到关注列表页面
    """
    logger.info('='*40 + ' 取消关注 ' + '='*40)
    
    current_user_id = session['uid']
    logger.info(f'当前用户 {current_user_id} 取消关注用户 {fuid}')
    
    try:
        dbutils.del_follow(current_user_id, fuid)
        logger.info(f'成功取消关注用户 {fuid}')
        flash('已取消关注')
    except Exception as e:
        logger.error(f'取消关注用户 {fuid} 时出错: {str(e)}')
        flash('取消关注失败，请稍后再试')
    
    return redirect(url_for('blog.get_follows'))


@bp.route('/sou', methods=['GET', 'POST'])
def sousuo():
    """搜索功能。
    
    支持GET和POST请求，搜索用户名。
    
    Returns:
        搜索结果页面
    """
    logger.info('='*40 + ' 搜索请求 ' + '='*40)
    
    value = None
    results = None
    
    # 处理搜索请求
    if request.method == 'POST':
        try:
            value = request.form.get('tkey', '')
            logger.info(f'搜索内容: {value}')
            
            # 输入验证
            if not value:
                logger.warning('搜索内容为空')
                flash('请输入搜索内容')
            else:
                # 执行搜索
                results = list(dbutils.db.user.find({'screen_name': {'$regex': value}}))
                logger.info(f'搜索到 {len(results)} 个结果')
        except Exception as e:
            logger.error(f'搜索时出错: {str(e)}')
            flash('搜索过程中发生错误，请稍后再试')
    
    # 准备模板数据
    para = {
        'users1': results,
        'value': value,
        'items': dbutils.get_hot(),
        'users': dbutils.random_user(10),
    }
    
    return render_template('blog/sou.html', dicts=para)


@bp.route('/send', methods=['POST'])
def send():
    """处理用户反馈。
    
    接收并存储用户发送的反馈信息。
    
    Returns:
        搜索页面
    """
    logger.info('='*40 + ' 接收用户反馈 ' + '='*40)
    
    try:
        msg = request.form.get('msg', '')
        
        if not msg:
            logger.warning('反馈内容为空')
            flash('请输入反馈内容')
            return render_template('blog/sou.html')
        
        logger.info(f'反馈内容: {msg}')
        
        # 记录反馈到文件
        with open('liuyan.txt', 'a+', encoding='utf-8') as f:
            f.write(f'{msg}\n')
        
        logger.info('反馈已记录')
        flash('感谢您的反馈！')
    except Exception as e:
        logger.error(f'处理反馈时出错: {str(e)}')
        flash('处理反馈时出错，请稍后再试')
    
    return render_template('blog/sou.html')