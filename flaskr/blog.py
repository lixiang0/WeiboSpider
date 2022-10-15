import flaskr
from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session
from werkzeug.exceptions import abort
from flask_cors import CORS, cross_origin
from flaskr.auth import login_required
from flaskr import dbutils

import logging
LOG = logging.getLogger(__name__)
bp = Blueprint("blog", __name__)




@bp.route('/')
def index():
    # count,authors=db.mblog.counts()
    # return render_template('base1.html')#,count=count,authors=authors)
    if 'uid' in session:
        return redirect(url_for('blog.uindex'))
    para={
        'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
    }
    return render_template('auth/login.html',dicts=para)


@bp.route('/u/<uid>')
@bp.route('/u')
@cross_origin()
@login_required
def uindex(uid=None):
    '''
    作用：用户首页
    参数：uid，可以为空；
    return：
    '''
    pagenum=int(request.args.get('page',0))
    if pagenum<0:
        pagenum=0
    # pagenum-=1
    LOG.info('-'*100)
    LOG.info('action:用户首页')
    LOG.info(f'uid:{uid}')
    LOG.info(f'pagenum:{pagenum}')
    userinfo=None
    blogs=[]
    _ulist=[]
    follow=False
    if uid:
        LOG.info('uid不为空，显示uid的主页，只获取用户信息')
        userinfo=dbutils.get_user(uid=uid)
        _ulist=[int(uid)]
        follow=True if int(uid) in  [int(u['blogger']) for u in list(dbutils.get_follows(int(session['uid'])))] else False
    else :
        LOG.info(f"登录用户为{int(session['uid'])}")
        LOG.info(f'uid为空，但已登录，显示登录用户主页，获取用户和关注信息')
        #注意：这里有可能userinfo为空，因为uid是用户注册设置的
        _ulist = [u['blogger'] for u in dbutils.get_follows(session['uid'])]
    LOG.info(f"关注信息为{_ulist}")
    _datas=dbutils.get_page(_ulist,pagenum)
    # print(_datas)
    for data in _datas:
        _,video_name=dbutils.net.video.extract(data)
        if video_name is not None:
            data['video_name']=video_name
        if 'retweeted_status' in data:
            data['retweeted_status']['video_name']=video_name
        blogs.append(data)
        LOG.info(data)
    LOG.info('END')
    LOG.info(len(blogs))
    LOG.info(userinfo)
    LOG.info('-'*100)
    para={
        'follow':follow,
        'blogs':list(blogs),
        'curr':pagenum,
        'user':userinfo,
        'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
    }
    return render_template('base.html',dicts=para)

    

@bp.route('/f/<uid>')
@bp.route('/f')
@login_required
@cross_origin()
def get_follows(uid=None):
    uid=session['uid']
    LOG.info(f'uid:{uid}')
    follows =  [int(u['blogger']) for u in list(dbutils.get_follows(int(session['uid'])))]
    LOG.info(f'follows:{follows}')
    users = dbutils.get_users(list(follows))
    LOG.info(f'users:{users}')
    para={
        # 'blogs':list(blogs),
        'follow':True,
        'users1':users,
        'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
    }
    return render_template('blog/follows.html',dicts=para)


@bp.route('/r/blog/<num>')
@cross_origin()
def get_random_20(num):
    blogs=dbutils.random_blog(num)
    para={
        'blogs':list(blogs),
        'curr':0,
        # 'user':userinfo,
        'items':dbutils.get_hot(),
        # 'users':dbutils.random_user(10),
    }
    return render_template('base.html',dicts=para)



@bp.route('/r/f/<num>')
@cross_origin()
def get_random_follows(num):
    users = dbutils.random_user(num)
    para={
        # 'blogs':list(blogs),
        # 'curr':pagenum,
        # 'user':userinfo,
        # 'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
    }
    return render_template('blog/follows.html',dicts=para)
@bp.route('/about')
def about():
    count=dbutils.db.mblog.counts()
    authors=dbutils.db.user.counts()
    states=dbutils.db.states.find({})
    para={
        'count':count,
        'authors':authors,
        'user':None,
        'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
        'states':dbutils.db.states.find({})
    }
    return render_template('about.html',dicts=para)
    # return render_template('me.html')
@bp.route('/hot/<url>')
def hot(url):
    print(url)
    mblogs=[]
    count=dbutils.db.mblog.count({})
    authors=dbutils.db.user.count({})
    url=f'https://weibo.com/a/hot/{url}'
    bids=dbutils.get_hot_bids(url)
    LOG.info(bids)
    for bid in bids:
        # utils.download_mblog({'bid':bid,'isLongText':True},'uid','current_page','total_page')
        mblog=dbutils.get_mblog_bid(bid)
        if mblog:
            _, video_name = dbutils.net.video.extract(mblog)
            if video_name is not None:
                mblog['video_name']=video_name
            if 'retweeted_status' in mblog:
                mblog['retweeted_status']['video_name']=video_name
            # print(mblog)
            mblogs.append(mblog)
    para={
        'blogs':list(mblogs),
        'count':count,
        'authors':authors,
        'curr':1,
        'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
    }
    return render_template('base.html',dicts=para)
@bp.route('/b/<bid>')
def blog(bid):
    mblog=dbutils.get_mblog_bid(bid)
    _, video_name = dbutils.net.video.extract(mblog)
    if video_name is not None:
        mblog['video_name']=video_name
    if 'retweeted_status' in mblog:
        mblog['retweeted_status']['video_name']=video_name
    comments=dbutils.get_comment(mblog['_id'])
    para={
        'blogs':[mblog],
        'comments':comments,
        # 'user':userinfo,
        'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
    }
    return render_template('blog/index.html',dicts=para)
@bp.route('/fav/<bid>')
@bp.route('/fav')
@login_required
def fav(bid=None):
    print('bid:',bid)
    if 'uid' in session:
        LOG.info('login in '+str(session['uid']))
        if bid:
            # LOG.info(db.fav.find({'uid':session['uid'],'bid':bid}))
            if dbutils.is_fav(session['uid'],bid):
                return 'fav duplicated'
            dbutils.add_fav(session['uid'],bid)
            return 'success'
        else:
            bids=[item['bid'] for item in dbutils.get_fav(session['uid'])]
            LOG.info(bids)
            mblogs = dbutils.get_mblog_bids(bids)
            # print(list(mblogs))
            para={
                'blogs':list(mblogs),
                'fav':True,
                'curr':1,
                'items':dbutils.get_hot(),
                'users':dbutils.random_user(10),
            }
            return render_template('base.html',dicts=para)
    else:
        return redirect(url_for('auth.login'))
# {'_id': str(uid)+str(user['id']), 'fans': int(uid), 'blogger': int(user['id'])}
@bp.route('/follow/<fuid>')
@login_required
def follow(fuid):
    LOG.info('执行关注操作\n*****************************************')
    LOG.info(f'关注用户:{fuid}')
    if 'uid' in session:
        uid=session['uid']
        LOG.info(f'登录用户:{uid}')
        if fuid:
            if dbutils.is_follow(uid,fuid):
                return 'follow duplicated'
            if not dbutils.add_follow(uid,fuid):
                LOG.info('add failed..')
            return redirect(url_for('blog.get_follows'))
    else:
        return redirect(url_for('auth.login'))
@bp.route('/ufav/<fbid>')
@login_required
def ufav(fbid):
    dbutils.del_fav(session['uid'],fbid)
    return redirect(url_for('fav'))

@bp.route('/ufollow/<fuid>')
@login_required
def ufollow(fuid):
    uid=session['uid']
    dbutils.del_follow(uid,fuid)
    return redirect(url_for('get_follows'))

@bp.route('/sou', methods=[ 'GET','POST'])
def sousuo():
    value=None
    ttype=None
    LOG.info('搜索')
    if request.method == 'POST':
        # print(dict(request.form))
        value=request.form['tkey']
        LOG.info('搜索内容:'+value)
        # ttype=request.form['ttype']

    results=None
    # print(value,ttype)
    if value:
        results=list(dbutils.db.user.find({'screen_name':{'$regex':value}}))
    # results=list(youran.db.mblog.db_mblogs.find({'text':{'$regex':value}}).limit(20))
    LOG.info('搜索结果:')
    LOG.info(results)
    para={
        # 'blogs':list(blogs),
        'users1':results,
        'value':value,
        'items':dbutils.get_hot(),
        'users':dbutils.random_user(10),
    }
    return render_template('blog/sou.html',dicts=para)

@bp.route('/send', methods=['POST'])
def send():
    LOG.info('接收到意见：')
    msg=request.form['msg']
    LOG.info('内容：'+msg)
    open('liuyan.txt','a+').write('1'+'\n')
    return render_template('blog/sou.html')