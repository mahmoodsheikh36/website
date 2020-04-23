from flask import Flask, request
import os
import json

from . import db

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
        db.add_request(ip, referrer, data, form, url, access_route, headers)
        print('request from: {}'.format(ip))

    db.init_app(app)

    from . import home
    app.register_blueprint(home.bp)

    from . import static
    app.register_blueprint(static.bp)

    from . import music
    app.register_blueprint(music.bp)

    @app.after_request
    def add_header(r):
        r.headers["Pragma"] = "no-cache"
        r.headers["Expires"] = "0"
        r.headers['Cache-Control'] = 'public, max-age=0'
        return r

    return app

application = create_app()
