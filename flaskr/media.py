from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import session,send_file
from werkzeug.exceptions import abort
import io
from flask_cors import CORS, cross_origin
from flaskr.auth import login_required
from flaskr.db import get_media
import logging
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