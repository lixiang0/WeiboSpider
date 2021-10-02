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
import youran
from youran import db,net
from youran.db import user,follow,hot,mblog,states,fav,comment,count,hotids
from youran.net import video
import logging
LOG = logging.getLogger(__name__)
bp = Blueprint("blog", __name__)


@bp.route('/')
def index():
    # count,authors=db.mblog.counts()
    # return render_template('base1.html')#,count=count,authors=authors)
    if 'uid' in session:
        return redirect(url_for('blog.uindex'))
    return render_template('auth/login.html',items=db.hot.find_hot()[0]['items'])


@bp.route('/u/<uid>')
@bp.route('/u')
@cross_origin()
@login_required
def uindex(uid=None):
    pagenum=int(request.args.get('page',1))
    if pagenum<1:
        pagenum=1
    LOG.info('-'*100)
    LOG.info('action:用户首页')
    LOG.info(f'uid:{uid}')
    LOG.info(f'pagenum:{pagenum}')
    userinfo=None
    blogs=[]
    hots=youran.db.hot.find_hot()[0]['items']

    _ulist=[]
    if uid:
        LOG.info('uid不为空，显示uid的主页，只获取用户信息')
        userinfo=youran.db.user.find_user(int(uid))
        _ulist=[int(uid)]
    else :
        
        userinfo=youran.db.user.find_user(str(session['uid']))
        LOG.info(f'uid为空，但已登录，显示登录用户主页，获取用户和关注信息')
        LOG.info(f"登录用户为{int(session['uid'])}")
        #注意：这里有可能userinfo为空，因为uid是用户注册设置的
        _ulist = youran.db.follow.follows(int(session['uid']))
        LOG.info(f"关注信息为{_ulist}")
    _datas=list(youran.db.mblog.latest(_ulist,pagenum-1))
    for data in _datas:
        _,video_name=youran.net.video.extract(data)
        if video_name is not None:
            data['video_name']=video_name
        if 'retweeted_status' in data:
            data['retweeted_status']['video_name']=video_name
        blogs.append(data)
    LOG.info('END')
    # LOG.info(blogs)
    LOG.info(userinfo)
    LOG.info('-'*100)
    return render_template('base.html',blogs=list(blogs),curr=pagenum,user=userinfo,items=hots)

    

@bp.route('/f/<uid>')
@bp.route('/f')
@login_required
@cross_origin()
def get_follows(uid=None):
    uid=session['uid']
    follows = db.follow.follows(int(uid))
    # print(follows)
    users = db.user.find_users(list(follows))
    # print(list(users))
    return render_template('blog/follows.html',users=list(users),follow=True,items=db.hot.find_hot()[0]['items'])


@bp.route('/r/blog/<num>')
@cross_origin()
def get_random_20(num):
    blogs=list(db.mblog.random(int(num)))
    # for blog in blogs:
        
    #     utils.download_media(blog)
    #     _, video_name = youran.net.video.extract(blog)
    #     if 'retweeted_status' in blog:
    #         if 'page_info' in blog['retweeted_status']:
    #             if 'media_info' in blog['retweeted_status']['page_info']:
    #                 blog['retweeted_status']['page_info']['media_info']['stream_url_hd']=video_name
    return render_template('base.html',blogs=blogs,items=db.hot.find_hot()[0]['items'])



@bp.route('/r/f/<num>')
@cross_origin()
def get_random_follows(num):
    # print(follows)
    users = db.user.random(int(num))
    # print(list(users))
    # return {'datas': list(users)}
    return render_template('blog/follows.html',users=list(users))
@bp.route('/about')
def about():
    count=db.mblog.db_mblogs.find({}).count()
    authors=db.user.count()
    states=db.states.finds()
    return render_template('about.html',count=count,authors=authors,user=None,states=states,items=db.hot.find_hot()[0]['items'])
    # return render_template('me.html')
@bp.route('/hot/<url>')
def hot(url):
    print(url)
    mblogs=[]
    count,authors=db.mblog.counts()
    bids=list(db.hotids.find_ids(url+"?type=grab"))[0]['bids']
    print(bids)
    for bid in bids:
        # utils.download_mblog({'bid':bid,'isLongText':True},'uid','current_page','total_page')
        mblog=db.mblog.db_mblogs.find_one({'bid':bid})
        _, video_name = net.video.extract(mblog)
        if video_name is not None:
            mblog['video_name']=video_name
        if 'retweeted_status' in mblog:
            mblog['retweeted_status']['video_name']=video_name
        # print(mblog)
        mblogs.append(mblog)
    return render_template('base.html',blogs=list(mblogs),count=count,authors=authors,curr=1)
@bp.route('/b/<bid>')
def blog(bid):
    mblog=db.mblog.db_mblogs.find_one({'bid':bid})
    _, video_name = net.video.extract(mblog)
    if video_name is not None:
        mblog['video_name']=video_name
    if 'retweeted_status' in mblog:
        mblog['retweeted_status']['video_name']=video_name
    comments=db.comment.find_comments(mblog['_id'])
    # print(comments)
    return render_template('blog/index.html',blog=mblog,comments=comments,items=db.hot.find_hot()[0]['items'])
@bp.route('/fav/<bid>')
@bp.route('/fav')
@login_required
def fav(bid=None):
    print('bid:',bid)
    if 'uid' in session:
        print('login in ',session['uid'])
        if bid:
            print(db.fav.find({'uid':session['uid'],'bid':bid}))
            if db.fav.find({'uid':session['uid'],'bid':bid}):
                return 'fav duplicated'
            db.fav.add({'uid':session['uid'],'bid':bid})
            return 'success'
        else:
            bids=[item['bid'] for item in list(db.fav.bids(session['uid']))]
            print(bids)
            mblogs = db.mblog.bids(bids)
            # print(list(mblogs))
            return render_template('base.html',blogs=list(mblogs),items=db.hot.find_hot()[0]['items'],fav=True,curr=1)
    else:
        return redirect(url_for('auth.login'))
# {'_id': str(uid)+str(user['id']), 'fans': int(uid), 'blogger': int(user['id'])}
@bp.route('/follow/<fuid>')
@login_required
def follow(fuid):
    print('fuid:',fuid)
    if 'uid' in session:
        print('login in ',session['uid'])
        if fuid:
            uid=session['uid']
            obj= {'_id': str(uid)+str(fuid), 'fans': int(uid), 'blogger': int(fuid)}
            print(db.follow.find(obj))
            if db.follow.find(obj):
                return 'follow duplicated'
            db.follow.add(obj)
            return redirect(url_for('blog.get_follows'))
    else:
        return redirect(url_for('auth.login'))
@bp.route('/ufav/<fbid>')
@login_required
def ufav(fbid):
    # uid=session['uid']
    obj={'uid':session['uid'],'bid':fbid}
    db.fav.delete(obj)
    return redirect(url_for('fav'))

@bp.route('/ufollow/<fuid>')
@login_required
def ufollow(fuid):
    uid=session['uid']
    obj= {'_id': str(uid)+str(fuid), 'fans': int(uid), 'blogger': int(fuid)}
    db.follow.delete(obj)
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
        results=list(youran.db.user.db_user.find({'screen_name':{'$regex':value}}))
    # results=list(youran.db.mblog.db_mblogs.find({'text':{'$regex':value}}).limit(20))
    LOG.info('搜索结果:')
    LOG.info(results)
    return render_template('blog/sou.html',users=results,value=value)

@bp.route('/send', methods=['POST'])
def send():
    LOG.info('接收到意见：')
    msg=request.form['msg']
    LOG.info('内容：'+msg)
    open('liuyan.txt','a+').write('1'+'\n')
    return render_template('blog/sou.html')

# @bp.route("/")
# def index():
#     """Show all the posts, most recent first."""
#     db = db
#     posts = db.execute(
#         "SELECT p.id, title, body, created, author_id, username"
#         " FROM post p JOIN user u ON p.author_id = u.id"
#         " ORDER BY created DESC"
#     ).fetchall()
#     return render_template("blog/index.html", posts=posts)


# def get_post(id, check_author=True):
#     """Get a post and its author by id.

#     Checks that the id exists and optionally that the current user is
#     the author.

#     :param id: id of post to get
#     :param check_author: require the current user to be the author
#     :return: the post with author information
#     :raise 404: if a post with the given id doesn't exist
#     :raise 403: if the current user isn't the author
#     """
#     post = (
#         db
#         .execute(
#             "SELECT p.id, title, body, created, author_id, username"
#             " FROM post p JOIN user u ON p.author_id = u.id"
#             " WHERE p.id = ?",
#             (id,),
#         )
#         .fetchone()
#     )

#     if post is None:
#         abort(404, f"Post id {id} doesn't exist.")

#     if check_author and post["author_id"] != g.user["id"]:
#         abort(403)

#     return post


# @bp.route("/create", methods=("GET", "POST"))
# @login_required
# def create():
#     """Create a new post for the current user."""
#     if request.method == "POST":
#         title = request.form["title"]
#         body = request.form["body"]
#         error = None

#         if not title:
#             error = "Title is required."

#         if error is not None:
#             flash(error)
#         else:
#             db = db
#             db.execute(
#                 "INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)",
#                 (title, body, g.user["id"]),
#             )
#             db.commit()
#             return redirect(url_for("blog.index"))

#     return render_template("blog/create.html")


# @bp.route("/<int:id>/update", methods=("GET", "POST"))
# @login_required
# def update(id):
#     """Update a post if the current user is the author."""
#     post = get_post(id)

#     if request.method == "POST":
#         title = request.form["title"]
#         body = request.form["body"]
#         error = None

#         if not title:
#             error = "Title is required."

#         if error is not None:
#             flash(error)
#         else:
#             db = db
#             db.execute(
#                 "UPDATE post SET title = ?, body = ? WHERE id = ?", (title, body, id)
#             )
#             db.commit()
#             return redirect(url_for("blog.index"))

#     return render_template("blog/update.html", post=post)


# @bp.route("/<int:id>/delete", methods=("POST",))
# @login_required
# def delete(id):
#     """Delete a post.

#     Ensures that the post exists and that the logged in user is the
#     author of the post.
#     """
#     get_post(id)
#     db = db
#     db.execute("DELETE FROM post WHERE id = ?", (id,))
#     db.commit()
#     return redirect(url_for("blog.index"))
