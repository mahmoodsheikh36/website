from flask import Flask, request, g, render_template
import os
import json
import datetime

from . import db
from . import auth
from website.utils import current_time

DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S:%f"

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'data.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    @app.before_request
    def log_request():
        auth.load_user_if_logged_in()

        ip = None

        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            ip = request.environ['REMOTE_ADDR']
        else:
            ip = request.environ.get('HTTP_X_FORWARDED_FOR')

        headers = json.dumps({k:v for k, v in request.headers.items()}, indent=2)
        data = request.data.decode('UTF-8')
        form = json.dumps(request.form.to_dict(flat=False), indent=2)
        access_route = json.dumps(request.access_route, indent=2)
        referrer = request.referrer
        url = request.url
        user_id = None
        if g.user:
            user_id = g.user['id']
        
        sql = \
        """
        INSERT INTO requests
        (ip, referrer, time_added, request_data, form,
        url, access_route, headers, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        values = (ip, referrer, current_time(), data, form, url, access_route, headers, user_id)
        db.get_db().execute(sql, values)
        db.get_db().commit()

        print('request from: {}:{}'.format(ip, datetime.datetime.now()))

    db.init_app(app)

    from . import home
    app.register_blueprint(home.bp)

    from . import static
    app.register_blueprint(static.bp)

    app.register_blueprint(auth.bp)

    from . import music
    app.register_blueprint(music.bp)

    from . import media
    app.register_blueprint(media.bp)

    @app.after_request
    def add_header(r):
        """
        Add headers to both force latest IE rendering engine or Chrome Frame,
        and also to cache the rendered page for 10 minutes.
        """
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    return app

application = create_app()
