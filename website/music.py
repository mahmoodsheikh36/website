import functools
from flask import current_app as app
from flask import (
    Blueprint, Response, request, send_from_directory, send_file
)
from werkzeug.utils import secure_filename
import os
import sqlite3
import json
import uuid

from website import auth
from website import db
from website.utils import current_time

bp = Blueprint('music', __name__, url_prefix='/music')

def check_auth(request_form, request_method=None, allow_anonymous=False):
    username = None
    password = None
    error_message = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']

    is_mahmooz = allow_anonymous and (username == 'mahmooz' or request_method == 'GET')

    if not username and not is_mahmooz:
        error_message = 'no username provided'
    elif not password and not is_mahmooz:
        error_message = 'no password provided'

    user = None
    if not is_mahmooz:
        user = auth.get_user_by_credentials(username, password)
        if user is None:
            error_message = 'wrong credentials'
    else:
        user = db.get_user_by_username('mahmooz')
        if user is None:
            error_message = 'mahmooz (admin) user hasn\'t been created yet'

    return user, error_message

@bp.route('/albums_prettified', methods=('POST', 'GET'))
def get_albums_prettified_route():
    user, error_message = check_auth(request.form,
                                     request_method=request.method,
                                     allow_anonymous=True)
    if error_message:
        return error_message
    db_albums = db.get_user_albums(user['id'])
    albums = []
    for db_album in db_albums:
        album = {}
        album['id'] = db_album['id']
        album['name'] = db_album['name']
        album['artist_id'] = db_album['artist_id']
        album['time_added'] = db_album['time_added']
        db_album_songs = db.get_album_songs(album['id'])
        album_songs = []
        for db_album_song in db_album_songs:
            db_song = db.get_song(db_album_song['song_id'])
            song = {}
            song['id'] = db_song['id']
            song['name'] = db_song['name']
            song['lyrics'] = db_song['lyrics']
            song['time_added'] = db_song['time_added']
            song_artists = []
            song_artist_relation = db.get_song_artists(song['id'])
            for song_artist in song_artist_relation:
                db_artist = db.get_artist(song_artist['artist_id'])
                artist = {}
                artist['name'] = db_artist['name']
                artist['time_added'] = db_artist['time_added']
                song_artists.append(artist)
            song['artists'] = song_artists
            album_songs.append(song)
        album['songs'] = album_songs
        albums.append(album)
    return Response(json.dumps(albums), mimetype='application/json')

@bp.route('/albums', methods=('POST', 'GET'))
def get_albums_route():
    user, error_message = check_auth(request.form,
                                     request_method=request.method,
                                     allow_anonymous=True)
    if error_message:
        return error_message
    db_albums = db.get_user_albums(user['id'])
    albums = []
    for db_album in db_albums:
        album = {}
        album['id'] = db_album['id']
        album['name'] = db_album['name']
        album['artist_id'] = db_album['artist_id']
        album['time_added'] = db_album['time_added']
        albums.append(album)
    return Response(json.dumps(albums), mimetype='application/json')

@bp.route('/metadata', methods=('POST', 'GET'))
def metadata_route():
    user, error_message = check_auth(request.form,
                                     request_method=request.method,
                                     allow_anonymous=True)
    if error_message:
        return error_message

    after_time = request.args.get('after_time')
    
    metadata = {}
    db_albums = db.get_user_albums(user['id'], after_time)
    metadata['albums'] = db_albums

    db_artists = db.get_user_artists(user['id'], after_time)
    metadata['artists'] = db_artists

    db_songs = db.get_user_songs(user['id'], after_time)
    metadata['songs'] = db_songs

    db_song_artists = db.get_user_song_artists(user['id'], after_time)
    metadata['song_artists'] = db_song_artists

    db_album_songs = db.get_user_album_songs(user['id'], after_time)
    metadata['album_songs'] = db_album_songs

    db_single_songs = db.get_user_single_songs(user['id'], after_time)
    metadata['single_songs'] = db_single_songs

    db_song_images = db.get_user_song_images(user['id'], after_time)
    metadata['song_images'] = db_song_images

    db_album_images = db.get_user_album_images(user['id'], after_time)
    metadata['album_images'] = db_album_images

    db_song_audio = db.get_user_song_audio(user['id'], after_time)
    metadata['song_audio'] = db_song_audio

    db_playlists = db.get_user_playlists(user['id'], after_time)
    metadata['playlists'] = db_playlists

    db_playlist_songs = db.get_user_playlist_songs(user['id'], after_time)
    metadata['playlist_songs'] = db_playlist_songs

    db_playlist_images = db.get_user_playlist_images(user['id'], after_time)
    metadata['playlist_images'] = db_playlist_images

    db_playlist_removals = db.get_user_playlist_removals(user['id'], after_time)
    metadata['playlist_removals'] = db_playlist_removals

    db_song_lyrics = db.get_user_song_lyrics(user['id'], after_time)
    metadata['song_lyrics'] = db_song_lyrics

    db_song_names = db.get_user_song_names(user['id'], after_time)
    metadata['song_names'] = db_song_names

    db_liked_songs = db.get_user_liked_songs(user['id'], after_time)
    metadata['liked_songs'] = db_liked_songs

    db_liked_song_removals = db.get_user_liked_song_removals(user['id'], after_time)
    metadata['liked_song_removals'] = db_liked_song_removals

    db_playlist_song_additions = db.get_playlist_song_additions(user['id'], after_time)
    metadata['playlist_song_additions'] = db_playlist_song_additions

    db_playlist_song_removals = db.get_playlist_song_removals(user['id'], after_time)
    metadata['playlist_song_removals'] = db_playlist_song_removals

    return Response(json.dumps(metadata), mimetype='application/json')

@bp.route('/add_playlist', methods=('POST',))
def add_playlist_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return error

    playlist_name = request.args.get('name')
    if playlist_name is None:
        return {'success': False, 'error': 'playlist name wasnt provided'}

    image_file = None
    original_image_file_name = None
    image_comment = None
    if 'image' in request.files:
        image_file = request.files['image']
    else:
        return { 'success': False, 'error': 'no image provided' }

    image_file_id = db.add_user_static_file(
            user['id'],
            image_file,
            None,
            None)
    playlist_id = db.add_playlist(user['id'], playlist_name)
    db.add_playlist_image(playlist_id, image_file_id)

    return {'success': True, 'data': {'id': playlist_id}}

@bp.route('/add_artist', methods=('POST',))
def add_artist():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    artist_name = request.args.get('name')
    if artist_name is None:
        return {'success': False, 'error': 'please provide the artist\'s name'}

    artist_id = db.add_artist(artist_name, user['id'])
    return {'success': True, 'data': {'id': artist_id}}

@bp.route('/add_album', methods=('POST',))
def add_album_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    album_name = request.args.get('album_name')
    artist_id = request.args.get('artist_id')
    album_image_file = None

    if album_name is None:
        return {'success': False, 'error': 'no album_name provided'}
    if artist_id is None:
        return {'success': False, 'error': 'no artist_id provided'}

    if 'image' not in request.files:
        return {'success': False, 'error': 'no image provided'}
    else:
        album_image_file = request.files['image']

    try:
        artist_id = int(artist_id)
    except ValueError as e:
        return {'success': False, 'error': 'artist_id should be an integer'}
    artist = db.get_artist(artist_id)
    if artist is None:
        return {'success': False, 'error': 'no such artist'}

    album = db.get_user_album(user['id'], album_name, artist_id)
    if album is not None:
        return {'success': False, 'error': 'album with this name exists for this artist already'}

    album_id = db.add_album(user['id'], album_name, artist_id)
    album_image_file_id = db.add_user_static_file(
            user['id'],
            album_image_file,
            None,
            None)
    db.add_album_image(album_id, album_image_file_id)

    return {'success': True, 'data': {'album_id': album_id}}

@bp.route('/add_song_to_album', methods=('POST',))
def add_song_to_album_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    album_id = request.args.get('album_id')
    if album_id is None:
        return {'success': False, 'error': 'no album_id provided'}
    try:
        album_id = int(album_id)
    except ValueError as e:
        return {'success': False, 'error': 'album_id should be an integer'}

    album = db.get_album(album_id)
    if album is None:
        return {'success': False, 'error': 'no album with id: ' + str(album_id)}

    song_audio_file = None
    if 'audio' not in request.files:
        return {'success': False, 'error': 'no audio file provided'}
    song_audio_file = request.files['audio']

    song_name = request.args.get('name')
    if song_name is None:
        return {'success': False, 'error': 'no song_name provided'}

    audio_duration = request.args.get('duration')
    if audio_duration is None:
        return {'success': False, 'error': 'the audio duration wasnt provided'}
    try:
        audio_duration = int(audio_duration)
    except ValueError as e:
        return {'success': False, 'error': 'duration should be an integer'}

    audio_bitrate = request.args.get('bitrate')
    if audio_bitrate is None:
        return {'success': False, 'error': 'audio bitrate wasn\'t provided'}
    try:
        audio_bitrate = int(audio_bitrate)
    except ValueError as e:
        return {'success': False, 'error': 'audio bitrate should be an integer'}

    index_in_album = request.args.get('index_in_album')
    if index_in_album is None:
        return {'success': False, 'error': 'song index in album wasnt provided'}
    try:
        index_in_album = int(index_in_album)
    except ValueError as e:
        return {'success': False, 'error': 'index_in_album should be an integer'}

    if db.get_album_song_by_index(album_id, index_in_album) is not None:
        return {'success': False, 'error': 'a song with this index already exists in this album'}

    artist_ids = []
    artist_ids_str = request.args.get('artist_ids')
    if artist_ids_str is None:
        return {'success': False, 'error': 'artist_ids not provided'}

    for artist_id_str in artist_ids_str.split(','):
        try:
            artist_ids.append(int(artist_id_str.strip()))
        except ValueError as e:
            return {'success': False, 'error': 'artist_id should be an integer'}

    for artist_id in artist_ids:
        artist = db.get_artist(artist_id)
        if artist is None:
            return {'success': False, 'error': 'no artist with id ' + str(artist_id)}

    song_id = db.add_song(user['id'])
    song_name_id = db.add_song_name(song_id, song_name)
    audio_file_id = db.add_user_static_file(
            user['id'],
            song_audio_file,
            None,
            None)
    db.add_song_audio(song_id, audio_file_id, audio_duration, audio_bitrate)
    for artist_id in artist_ids:
        db.add_song_artist(song_id, artist_id)
    db.add_album_song(song_id, album_id, index_in_album)
    db.add_song_image(song_id, db.get_album_image_file(album_id)['user_static_file_id'])

    return {'success': True, 'data': {'id': song_id}}

@bp.route('/add_single_song', methods=('POST',))
def add_single_song_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    song_audio_file = None
    if 'audio' in request.files:
        song_audio_file = request.files['audio']
    else:
        return {'success': False, 'error': 'no audio file provided'}

    song_name = request.args.get('name')
    if song_name is None:
        return {'success': False, 'error': 'song\'s name wasnt provided'}

    song_image_file = None
    if 'image' in request.files:
        song_image_file = request.files['image']
    else:
        return {'success': False, 'error': 'no image file provided'}

    artist_ids = []
    artist_ids_str = request.args.get('artist_ids')
    if artist_ids_str is None:
        return {'success': False, 'error': 'artist_ids not provided'}

    for artist_id_str in artist_ids_str.split(','):
        try:
            artist_ids.append(int(artist_id_str.strip()))
        except ValueError as e:
            return {'success': False, 'error': 'artist_id should be an integer'}

    for artist_id in artist_ids:
        artist = db.get_artist(artist_id)
        if artist is None:
            return {'success': False, 'error': 'no artist with id ' + str(artist_id)}

    audio_bitrate = request.args.get('bitrate')
    if audio_bitrate is None:
        return {'success': False, 'error': 'audio bitrate wasn\'t provided'}
    try:
        audio_bitrate = int(audio_bitrate)
    except ValueError as e:
        return {'success': False, 'error': 'audio bitrate should be an integer'}

    audio_duration = request.args.get('duration')
    if audio_duration is None:
        return {'success': False, 'error': 'the audio duration wasnt provided'}
    try:
        audio_duration = int(audio_duration)
    except ValueError as e:
        return {'success': False, 'error': 'duration should be an integer'}

    song_id = db.add_song(user['id'])
    song_name_id = db.add_song_name(song_id, song_name)
    image_file_id = db.add_user_static_file(
            user['id'],
            song_image_file,
            None,
            None)
    audio_file_id = db.add_user_static_file(
            user['id'],
            song_audio_file,
            None,
            None)
    db.add_song_audio(song_id, audio_file_id, audio_duration, audio_bitrate)
    db.add_song_image(song_id, image_file_id)
    single_song_id = db.add_single_song(song_id)
    for artist_id in artist_ids:
        db.add_song_artist(song_id, artist_id)

    return {'success': True, 'data': {'id': song_id}}

@bp.route('/like_song', methods=('POST',))
def like_song_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    song_id = request.args.get('id')
    if song_id is None:
        return {'success': False, 'error': 'no song_id provided'}
    try:
        song_id = int(song_id)
    except ValueError as e:
        return {'success': False, 'error': 'song_id should be an integer'}

    liked_songs_row_id = db.add_liked_song(song_id)
    return {'success': True, 'data': {'liked_songs_row_id': liked_songs_row_id}}

@bp.route('/add_song_to_playlist', methods=('POST',))
def add_song_to_playlist_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    playlist_id = request.args.get('playlist_id')
    if playlist_id is None:
        return {'success': False, 'error': 'please provide the playlists id'}
    song_id = request.args.get('song_id')
    if song_id is None:
        return {'success': False, 'error': 'please provide the songs id that u want add to the playlist'}

    if db.get_playlist_song(playlist_id, song_id) is not None:
        return {'success': False, 'error': 'this song already exists in this playlist'}

    playlist_songs_row_id = db.add_playlist_song(playlist_id, song_id)
    return {'success': True, 'data': {'playlist_songs_row_id': playlist_song_row_id}}

@bp.route('/singles', methods=('POST',))
def singles_route():
    user, error = check_auth(request.form)
    if error:
        return error
    db_single_songs = db.get_user_single_songs(user['id'])
    single_songs = []
    for db_single_song in db_single_songs:
        single_song = {}
        db_song = db.get_song(db_single_song['song_id'])
        single_song['id'] = db_song['id']
        single_song['name'] = db_song['name']
        single_song['lyrics'] = db_song['lyrics']
        single_song['artist_id'] = db_song['name']
        single_songs.append(single_song)
    return Response(json.dumps(single_songs), mimetype='application/json')

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
        user = auth.get_user_by_credentials(username, password)
        if user is None:
            return 'wrong credentials'
    else:
        user = db.get_user_by_username('mahmooz')

    after_id = request.args.get('after_id')
    if after_id != None:
        try:
            db_songs = db.get_user_songs_after_id(int(user['id'], after_id))
        except ValueError as e:
            return Response('after_id has to be an integer')
    else:
        db_songs = db.get_user_songs(user['id'])

    songs = []
    for db_song in db_songs:
        song = {}
        song['id'] = db_song['id']
        song['name'] = db_song['name']
        song['artist'] = db_song['artist']
        song['album'] = db_song['album']
        song['lyrics'] = db_song['lyrics']
        first_song_audio = db.get_song_first_audio_file(song['id'])
        last_song_audio = db.get_song_last_audio(song['id'])
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
        user = auth.get_user_by_credentials(username, password)
        if user is None:
            return 'wrong credentials'
    else:
        user = db.get_user_by_username('mahmooz')

    song_id = request.args.get('song_id')
    if song_id is None:
        return 'please provide song_id as a query string'

    file_path = db.get_song_last_audio_file_path(song_id)
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
        user = auth.get_user_by_credentials(username, password)
        if user is None:
            return 'wrong credentials'
    else:
        user = db.get_user_by_username('mahmooz')

    song_id = request.args.get('song_id')
    if song_id is None:
        return 'please provide song_id as a query string'

    file_path = db.get_song_last_image_file_path(song_id)
    if file_path is None:
        return 'no image found for a song with an id of {}'.format(song_id)

    return send_file(file_path)
