import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

from website.db import get_db
from website.utils import current_time

bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_user_by_credentials(username, password):
    user = get_db().execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()

    if user is None or not password == user['password']:
        return None

    return user

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = None
        password = None
        email    = None

        if 'username' in request.form:
            username = request.form['username']
        if 'password' in request.form:
            password = request.form['password']
        if 'email' in request.form:
            email = request.form['email']

        error = None
            
        if not username:
            error = 'Username is required to register'
        if not password:
            error = 'Password is required to register'
        if not email:
            error = 'Email is required to register'

        if not error:
            db = get_db()

            if db.execute(
                    'SELECT id FROM users WHERE username = ?', (username,)
            ).fetchone() is not None:
                error = 'User {} is already registered'.format(username)

            if error is None:
                db.execute(
                    'INSERT INTO users (username, password, email, time_added) VALUES (?, ?, ?, ?)',
                    (username, password, email, current_time())
                )
                db.commit()
                return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = None
        password = None

        if 'username' in request.form:
            username = request.form['username']
        if 'password' in request.form:
            password = request.form['password']

        error = None

        if not username:
            error = 'Username is required to login'
        elif not password:
            error = 'Password is required to login'

        if not error:
            db = get_db()

            user = db.execute(
                'SELECT * FROM users WHERE username = ?', (username,)
            ).fetchone()

            if user is None:
                error = 'Incorrect username.'
            elif not password == user['password']:
                error = 'Incorrect password.'

            if error is None:
                session.clear()
                session['user_id'] = user['id']
                return redirect(url_for('home.index'))

        flash(error)

    return render_template('auth/login.html')

def load_user_if_logged_in():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home.index'))
