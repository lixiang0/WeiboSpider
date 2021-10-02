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
import logging
from flaskr.db import get_db
# from flaskr import blog
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
        ruser=get_db().count.find_user(uname)
        LOG.info('用户名密码与数据中进行比对结果：')
        LOG.info(ruser)
        if ruser:
            if ruser['uname']==uname and ruser['psw']==psw:
                LOG.info('登陆成功，转到主页，用户登陆成功')
                session['uid']=ruser['_id']
                LOG.info(f'当前登录用户为：{session["uid"]}')
                return redirect(url_for('blog.index'))
        else:
            return render_template('auth/login.html',items=get_db().hot.find_hot()[0]['items'])
    else:
        return render_template('auth/login.html',items=get_db().hot.find_hot()[0]['items'])
@bp.route('/logout', methods=[ 'GET','POST'])
def logout():
    session.pop('uid', None)
    return redirect(url_for('auth.login'))
@bp.route('/register', methods=[ 'GET','POST'])
def signup():
    print(request.form)
    if request.method == 'POST':
        u=get_db().user.find_user(request.form['uid'])
        print(u)
        if u:
            return render_template('auth/register.html',error='uid is duplicated')
        else:
            get_db().count.add_user({'_id':request.form['uid'],'uname':request.form['uname'],'psw':request.form['psw']})
            session['uid']=request.form['uid']
            return redirect(url_for('blog.index'))
    return render_template('auth/register.html')

# @bp.route("/register", methods=("GET", "POST"))
# def register():
#     """Register a new user.

#     Validates that the username is not already taken. Hashes the
#     password for security.
#     """
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]
#         db = get_db()
#         error = None

#         if not username:
#             error = "Username is required."
#         elif not password:
#             error = "Password is required."

#         if error is None:
#             try:
#                 db.execute(
#                     "INSERT INTO user (username, password) VALUES (?, ?)",
#                     (username, generate_password_hash(password)),
#                 )
#                 db.commit()
#             except db.IntegrityError:
#                 # The username was already taken, which caused the
#                 # commit to fail. Show a validation error.
#                 error = f"User {username} is already registered."
#             else:
#                 # Success, go to the login page.
#                 return redirect(url_for("auth.login"))

#         flash(error)

#     return render_template("auth/register.html")


# @bp.route("/login", methods=("GET", "POST"))
# def login():
#     """Log in a registered user by adding the user id to the session."""
#     if request.method == "POST":
#         username = request.form["username"]
#         password = request.form["password"]
#         db = get_db()
#         error = None
#         user = db.execute(
#             "SELECT * FROM user WHERE username = ?", (username,)
#         ).fetchone()

#         if user is None:
#             error = "Incorrect username."
#         elif not check_password_hash(user["password"], password):
#             error = "Incorrect password."

#         if error is None:
#             # store the user id in a new session and return to the index
#             session.clear()
#             session["user_id"] = user["id"]
#             return redirect(url_for("index"))

#         flash(error)

#     return render_template("auth/login.html")


# @bp.route("/logout")
# def logout():
#     """Clear the current session, including the stored user id."""
#     session.clear()
#     return redirect(url_for("index"))
