from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session,send_file
from flaskr import db, dbutils
from werkzeug.exceptions import abort
import io
from flask_cors import CORS, cross_origin
from flaskr.auth import login_required
from flaskr.db import get_media
import logging

import youran
LOG = logging.getLogger(__name__)
bp = Blueprint("media", __name__)



@bp.route('/static/<ttype>/<name>')
def download_file(ttype,name):
    # return send_from_directory(f'/mnt/data/weibo/{ttype}', name)
    return send_file(
        io.BytesIO(get_media().get_weibo_media(ttype,name)),
        mimetype='image/jpg',
        as_attachment=True,
        attachment_filename=name
    )
@bp.route('/download/<name>')
def download_bilibili(name):
    # return send_from_directory(f'/mnt/data/weibo/{ttype}', name)
    kv={'_id':name[:-4],'filename':name[:-4]}
    youran.logger.info(str(kv)+'*'*10)
    kvs=list(dbutils.find_count(kv))
    count=len(kvs)
    youran.logger.info(str(count)+'*'*10)
    kvv=kvs[0] if count>0 else {'count':0,'_id':name[:-4],'filename':name[:-4]}
    if count>0:
        kvv['count']=333
    else:
        kvv['count']=444
    dbutils.add_count(kvv)
    youran.logger.info(kvv)
    return send_file('static/'+name, as_attachment=True)

@bp.route('/files/<name>', methods=[ 'GET'])
@bp.route('/files', methods=[ 'GET','POST'])
def index(name=None):
    import time
    if request.method == 'POST':
        uname=request.form['uname']
        utext=request.form['utext']
        if uname not in session:
            session[uname]=time.time()
        else:
            if time.time()-session[uname]<10*60:
                return render_template('error.html',dicts=None)
        print(uname,utext)
        count=len(list(dbutils.find_liuyan()))
        dbutils.add_liuyan({
            '_id':count,
            'uname':uname,
            'utext':utext,
            'create_at':time.asctime( time.localtime(time.time()) ),
        })
        para={
            'liuyan':True,
            'items':list(dbutils.find_liuyan())
        }
        return render_template('files/index.html',dicts=para)
    else:
        items=dbutils.find_liuyan()
        if name!=None:
            templates={
                'bili1':'files/bili1.html',
                'bili2':'files/bili2.html',
                'bili3':'files/bili3.html'
            }
            kv={'_id':name}
            youran.logger.info(kv)
            count=list(dbutils.find_count(kv))
            youran.logger.info(list(count))
            if len(count)>0:
                count=count[0]['count']
            else:
                count=0
            para={
            'liuyan':False,
            'items':list(items),
            'count':count
            }
            youran.logger.info(repr(para))
            return render_template(templates[name],dicts=para)
        else:
            para={
            'liuyan':False,
            'items':list(items)
            }
            return render_template('files/index.html',dicts=para)