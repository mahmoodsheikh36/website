from flask import (
    Blueprint, session, send_from_directory
)

bp = Blueprint('static', __name__, url_prefix='')

@bp.route('/css/<path:path>')
def style(path):
    return send_from_directory('static/css', path)

@bp.route('/js/<path:path>')
def javascript(path):
    return send_from_directory('static/js', path)

@bp.route('/static/<path:path>')
def static_file_full_path(path):
    return send_from_directory('static', path)
