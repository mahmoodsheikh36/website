import functools
from flask import (
    Blueprint, Response, request, send_from_directory, send_file, url_for, g, render_template
)
from website.auth import login_required
from website import db
from website.music import check_auth

bp = Blueprint('media', __name__, url_prefix='/media')

@bp.route('/add_image', methods=('POST',))
def add_image_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    image_file = None
    if 'image' not in request.files:
        return {'success': False, 'error': 'no image file provided'}
    image_file = request.files['image']

    title = None
    if 'title' in request.form:
        title = request.form['title']

    file_id = db.add_user_static_file(user['id'], image_file)
    image_id = db.add_image(user['id'], file_id, title)

    return {'success': True, 'data': {'id': image_id}}

@bp.route('/add_image_to_collage', methods=('POST',))
def add_image_to_collage_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    collage_id = None
    if 'collage_id' not in request.form:
        return {'success': False, 'error': 'collage_id not provided'}
    collage_id = request.form['collage_id']

    image_id = None
    if 'image_id' not in request.form:
        return {'success': False, 'error': 'image_id not provided'}
    image_id = request.form['image_id']

    image = db.get_image(image_id)
    if image is None:
        return {'success': False, 'error': 'no image with such id'}

    collage = db.get_collage(collage_id)
    if collage is None:
        return {'success': False, 'error': 'no collage with such id'}

    db.add_collage_image(collage_id, image_id)

    return {'success': True, 'data': {}}

@bp.route('/collage/<int:id>', methods=('GET',))
@login_required
def collage_route(id):
    collage = db.get_collage(id)
    user = g.user
    if collage is None or collage['owner_id'] != user['id']:
        return 'no such collage'

    images = db.get_collage_images(id)

    collage_title = 'collage'
    if collage['title'] is not None:
        collage_title = collage['title']

    return render_template('collage.html',
            images=images, collage_title=collage_title)

@bp.route('/add_collage', methods=('POST',))
def add_collage_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    if 'title' not in request.form:
        return {'success': False, 'error': 'no title provided'}
    title = request.form['title']

    collage_id = db.add_collage(user['id'], title)

    return {'success': True, 'data': {'id': collage_id}}
