import os
import logging
from flask import Flask,session,send_file
import io

from werkzeug.utils import find_modules, import_string
def configure_logging():
    # register root logging
    logging.basicConfig(level=logging.INFO,filename='web.log',filemode='w')
    logging.getLogger('werkzeug').setLevel(logging.INFO)
def register_blueprints(app):
    """Automagically register all blueprint packages
    Just take a look in the blueprints directory.
    """
    for name in find_modules('blueprints', recursive=True):
        mod = import_string(name)
        if hasattr(mod, 'bp'):
            app.register_blueprint(mod.bp)
    return None
def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    configure_logging()

    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    

    # @app.route('/static/<ttype>/<name>')
    # def download_file(ttype,name):
    #     # return send_from_directory(f'/mnt/data/weibo/{ttype}', name)
    #     return send_file(
    #         io.BytesIO(min.get_weibo_media(ttype,name)),
    #         mimetype='image/jpg',
    #         as_attachment=True,
    #         attachment_filename=name
    #     )

    # register the database commands
    from flaskr import db

    # db.init_app(app)

    # apply the blueprints to the app
    from flaskr import auth, blog,media

    app.register_blueprint(auth.bp)
    app.register_blueprint(blog.bp)
    app.register_blueprint(media.bp)

    # make url_for('index') == url_for('blog.index')
    # in another app, you might define a separate main index here with
    # app.route, while giving the blog blueprint a url_prefix, but for
    # the tutorial the blog will be the main index
    # app.add_url_rule("/static/", endpoint="download_file")

    return app
if __name__ == "__main__":
    app = create_app(os.getenv('FLASK_CONFIG') or 'dev')
    app.run()