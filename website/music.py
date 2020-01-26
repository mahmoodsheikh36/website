import functools
from flask import current_app as app
from flask import (
    Blueprint, Response, request, send_from_directory, send_file
)
from werkzeug import secure_filename
import os
import sqlite3
import json
import uuid

from website.auth import get_user_by_credentials
from website.db import (
    add_user_static_file, add_song, get_user_songs, get_song_first_audio_file,
    get_song_last_audio_file_path, get_user_by_username, get_song_last_audio_file,
    get_song_last_audio, get_song_last_image_file_path, get_user_songs_after_id
)
from website.utils import current_time

bp = Blueprint('music', __name__, url_prefix='/music')

@bp.route('/add_song', methods=('POST',))
def add_song_route():
    username = None
    password = None
    audio_file = None
    song_name = None
    song_artist = None
    song_album = None
    audio_duration = None
    song_lyrics = None
    audio_comment = None
    image_comment = None
    image_file = None
    lyrics = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']
    if 'audio' in request.files:
        audio_file = request.files['audio']
    if 'name' in request.form:
        song_name = request.form['name']
    if 'artist' in request.form:
        song_artist = request.form['artist']
    if 'album' in request.form:
        song_album = request.form['album']
    if 'duration' in request.form:
        audio_duration = request.form['duration']
    if 'lyrics' in request.form:
        song_lyrics = request.form['lyrics']
    if 'audio_comment' in request.form:
        comment = request.form['audio_comment']
    if 'image_comment' in request.form:
        comment = request.form['image_comment']
    if 'image' in request.files:
        image_file = request.files['image']

    error = None

    if not username:
        error = 'huh? wheres the username?'
    if not password:
        error = '-_- u need a password'
    if not audio_file:
        error = 'provide an audio file goddamit!'
    if not song_name:
        error = 'you did not provide the songs name'
    if not song_artist:
        error = 'you did not provide the songs artist name'
    if not audio_duration:
        error = 'you did not provide the songs audio duration'
    if not song_album:
        error = 'you did not provide the songs album name'

    if error:
        return error

    user = get_user_by_credentials(username, password)
    if user is None:
        return 'wrong credentials'

    audio_file_id = add_user_static_file(user['id'], audio_file, audio_comment)
    image_file_id = add_user_static_file(user['id'], image_file, image_comment)

    song_id = add_song(user['id'], song_name, song_artist, song_album,
                       audio_file_id, image_file_id, audio_duration, song_lyrics)

    return 'OK {}, added song \'{}\' by \'{}\''.format(user['username'],
                                                       song_name,
                                                       song_artist)

@bp.route('/songs', methods=['POST'])
def all_songs_route():
    username = None
    password = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']

    is_mahmooz = username == 'mahmooz'

    if not username:
        return 'no username provided'
    elif not password and not is_mahmooz:
        return 'no password provided'

    user = None
    if not is_mahmooz:
        user = get_user_by_credentials(username, password)
        if user is None:
            return 'wrong credentials'
    else:
        user = get_user_by_username('mahmooz')

    after_id = request.args.get('after_id')
    if after_id != None:
        try:
            db_songs = get_user_songs_after_id(int(after_id))
        except ValueError as e:
            return Response('after_id has to be an integer')
    else:
        db_songs = get_user_songs(user['id'])

    songs = []
    for db_song in db_songs:
        song = {}
        song['id'] = db_song['id']
        song['name'] = db_song['name']
        song['artist'] = db_song['artist']
        song['album'] = db_song['album']
        song['lyrics'] = db_song['lyrics']
        first_song_audio = get_song_first_audio_file(song['id'])
        last_song_audio = get_song_last_audio(song['id'])
        song['date_added'] = first_song_audio['add_timestamp']
        song['duration'] = last_song_audio['duration']
        songs.append(song)

    return Response(json.dumps(songs), mimetype='application/json')

@bp.route('/audio', methods=['POST'])
def get_song_audio_route():
    username = None
    password = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']

    is_mahmooz = username == 'mahmooz'

    if not username:
        return 'no username provided'
    elif not password and not is_mahmooz:
        return 'no password provided'

    user = None
    if not is_mahmooz:
        user = get_user_by_credentials(username, password)
        if user is None:
            return 'wrong credentials'
    else:
        user = get_user_by_username('mahmooz')

    song_id = request.args.get('song_id')
    if song_id is None:
        return 'please provide song_id as a query string'

    file_path = get_song_last_audio_file_path(song_id)
    if file_path is None:
        return 'no audio found for a song with an id of {}'.format(song_id)

    return send_file(file_path)

@bp.route('/image', methods=['POST'])
def get_song_image_route():
    username = None
    password = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']

    is_mahmooz = username == 'mahmooz'

    if not username:
        return 'no username provided'
    elif not password and not is_mahmooz:
        return 'no password provided'

    user = None
    if not is_mahmooz:
        user = get_user_by_credentials(username, password)
        if user is None:
            return 'wrong credentials'
    else:
        user = get_user_by_username('mahmooz')

    song_id = request.args.get('song_id')
    if song_id is None:
        return 'please provide song_id as a query string'

    file_path = get_song_last_image_file_path(song_id)
    if file_path is None:
        return 'no image found for a song with an id of {}'.format(song_id)

    return send_file(file_path)
