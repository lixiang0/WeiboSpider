import os
# export   DBIP=192.168.8.101
# export   MINIOIP=192.168.8.101
# export   DBPort=27017 
# export  MINIOPort=9000
os.environ["DBIP"]="192.168.8.111"
os.environ["MINIOIP"]="192.168.8.111"
os.environ["DBPort"]="27017"
os.environ["MINIOPort"]="9000"
import logging
from flask import Flask,session,send_file
import io

from werkzeug.utils import find_modules, import_string

def configure_logging():
    # Register root logging
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    # Consider adding different handlers for different environments

def register_blueprints(app):
    """Automagically register all blueprint packages
    Just take a look in the blueprints directory.
    """
    try:
        for name in find_modules('blueprints', recursive=True):
            mod = import_string(name)
            if hasattr(mod, 'bp'):
                app.register_blueprint(mod.bp)
    except Exception as e:
        logging.error(f"Error registering blueprints: {e}")
    return None

def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    configure_logging()

    app.config.from_mapping(
        # A default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # Store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "flaskr.sqlite"),
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        try:
            app.config.from_pyfile("config.py", silent=True)
        except Exception as e:
            logging.error(f"Error loading config.py: {e}")
    else:
        # Load the test config if passed in
        app.config.update(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError as e:
        logging.error(f"Error creating instance path: {e}")
    

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
