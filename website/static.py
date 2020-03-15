from flask import (
    Blueprint, send_from_directory, request
)
from website.music import check_auth
from website import db

bp = Blueprint('static', __name__, url_prefix='/static')

@bp.route('/css/<path:path>')
def style(path):
    return send_from_directory('static/css', path)

@bp.route('/js/<path:path>')
def javascript(path):
    return send_from_directory('static/js', path)

@bp.route('/static/<path:path>')
def static_file_full_path(path):
    return send_from_directory('static', path)

@bp.route('/file/<int:file_id>')
def static_file(file_id):
    user, error_message = check_auth(request.form,
                                     request_method=request.method,
                                     allow_anonymous=True)
    if error_message:
        return error_message

    db_file = db.get_file(file_id)
    #if db_file['owner_id'] == user['id']:
    return send_from_directory(
            db.get_files_dir(),
            db_file['name'])
    #return 'you don\'t own this file'
