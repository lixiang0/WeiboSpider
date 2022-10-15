import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import logging,youran
from flaskr.db import get_db
from flaskr import dbutils
LOG = logging.getLogger(__name__)
bp = Blueprint("auth", __name__, url_prefix="/auth")

# @bp.before_app_request
# def load_logged_in_user():
#     """If a user id is stored in the session, load the user object from
#     the database into ``g.user``."""
#     user_id = session.get("user_id")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        LOG.info('-'*100)
        LOG.info('action:登录检测')
        if session.get("uid") is None:
            LOG.info('没有登录，转到登录界面')
            return redirect(url_for("auth.login"))
        LOG.info('已经登录，通过验证')
        LOG.info('*'*100)
        return view(**kwargs)
    
    return wrapped_view


@bp.route('/login', methods=[ 'GET','POST'])
def login():
    LOG.info('-'*100)
    LOG.info('action:login')
    if request.method == 'POST':
        LOG.info('接收到的前端FORM：')
        LOG.info(dict(request.form))
        uname=request.form['uname']
        psw=request.form['psw']
        ruser=get_db().account.find_user(uname)
        LOG.info('用户名密码与数据中进行比对结果：')
        LOG.info(ruser)
        if ruser:
            ruser=ruser[0]
            if ruser['uname']==uname and ruser['psw']==psw:
                LOG.info('登陆成功，转到主页，用户登陆成功')
                session['uid']=ruser['_id']
                LOG.info(f'当前登录用户为：{session["uid"]}')
                return redirect(url_for('blog.index'))
        else:
            return render_template('auth/login.html',dicts={'items':dbutils.get_hot()})
    else:
        return render_template('auth/login.html',dicts={'items':dbutils.get_hot()})
@bp.route('/logout', methods=[ 'GET','POST'])
def logout():
    session.pop('uid', None)
    return redirect(url_for('auth.login'))
@bp.route('/register', methods=[ 'GET','POST'])
def signup():
    print(request.form)
    if request.method == 'POST':
        u=get_db().user.find_users([request.form['uid']])
        # print(u)
        if u and u.count():
            return render_template('auth/register.html',error='uid is duplicated')
        else:
            get_db().account.add({'_id':request.form['uid'],'uname':request.form['uname'],'psw':request.form['psw']})
            session['uid']=request.form['uid']
            return redirect(url_for('blog.index'))
        
    return render_template('auth/register.html',dicts={'items':dbutils.get_hot()})
