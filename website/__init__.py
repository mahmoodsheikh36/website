import os

from flask import Flask, request
import json
import datetime

from . import db

DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S:%f"

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'website.sqlite'),
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
        ip = request.remote_addr
        headers = json.dumps({k:v for k, v in request.headers.items()}, indent=2)
        data = request.data.decode('UTF-8')
        form = json.dumps(request.form.to_dict(flat=False), indent=2)
        access_route = json.dumps(request.access_route, indent=2)
        referrer = request.referrer
        url = request.url
        request_date = datetime.datetime.now().strftime(DATETIME_FORMAT)
        remote_port = request.environ.get('REMOTE_PORT')
        
        sql = \
        """
        INSERT INTO request
        (ip, port, referrer, request_date, request_data, form,
        url, access_route, headers)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """

        values = (ip, port, referrer, request_date, data, form, url, access_route, headers)
        db.get_db().execute(sql, values)

        print('request from: {}:{}'.format(request.remote_addr, remote_port))

    db.init_app(app)

    from . import home
    app.register_blueprint(home.bp)

    return app
