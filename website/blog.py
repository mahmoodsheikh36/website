from flask import (
    Blueprint, render_template, request, g, redirect, url_for, abort, flash
)

from website.auth import login_required
from website.db import get_db

bp = Blueprint('blog', __name__, url_prefix='/blog')

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, admin_only'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)    

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = None
        body  = None
        admin_only = False
        error = None

        if not g.user['is_admin']:
            error = 'authorization failure, gfys'

        if 'title' in request.form:
            title = request.form['title']
        if 'body' in request.form:
            body = request.form['body']
        if 'admin_only' in request.form:
            if request.form['admin_only'] == 'yes':
                admin_only = True

        if not title and not error:
            error = 'Title is required to create a post'
        if not body and not error:
            error = 'body is required to create a post'

        if error:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id, admin_only)'
                ' VALUES (?, ?, ?, ?)',
                (title,
                 body,
                 g.user['id'],
                 1 if admin_only else 0)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, admin_only'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, "Post id {0} doesn't exist.".format(id))

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        error = None
        title = None
        body = None

        if not 'title' in request.form:
            error = 'title is required'
        if not 'body' in request.form:
            error = 'body is required'

        if not error:
            title = request.form['title']
            body = request.form['body']

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

@bp.route('/<int:id>/post')
def post(id):
    post = get_post(id, check_author=False)

    is_user_admin = g.user and g.user['is_admin']
    is_post_admin_only = post['admin_only']

    if is_post_admin_only and not is_user_admin:
        abort(403)
    return render_template('blog/post.html', post=post)
