import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for,
    send_from_directory
)

import json

from website.config import *
from website.spotify import get_tracks, get_access_token
from website.db import get_db

bp = Blueprint('home', __name__, url_prefix='/')

@bp.route('', methods=['GET'])
def index():
    return render_template('index.html')

@bp.route('index', methods=['GET'])
def index_page():
    return index()

@bp.route('spotify', methods=['GET', 'POST'])
def spotify():
    return redirect(SPOTIFY_URL)

@bp.route('github', methods=['GET', 'POST'])
def github():
    return redirect(GITHUB_URL)

@bp.route('youtube', methods=['GET', 'POST'])
def youtube():
    return redirect(YOUTUBE_URL)

@bp.route('music', methods=['GET'])
def music():
    return render_template('music.html', tracks=get_tracks())

@bp.route('music/json', methods=['GET'])
def music_json():
    return json.dumps(get_tracks())

@bp.route('music/spotify_access_token', methods=['POST'])
def spotify_access_token():
    username = None
    password = None
    
    error = 0

    if 'username' in request.form:
        username = request.form['username']
    else:
        error = 1

    if 'password' in request.form:
        password = request.form['password']
    else:
        error = 2

    if error == 0:
        db = get_db()

        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is not None and password == user['password']:
            return get_access_token()
        error = 3

    return 'fuck off' + error
