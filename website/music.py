import functools
from flask import current_app as app
from flask import (
    Blueprint, Response, request, send_from_directory, send_file
)

from website import auth
from website import db
from website.utils import current_time
from website.ffmpeg import get_audio_stream_format_data

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

def delete_song(song_id):
    song = db.get_song(song_id)
    db.delete_song(song_id)
    db.delete_file(song['audio_file_id'])
    db.delete_song_artists(song_id)

def delete_album(user_id, album_id):
    album = db.get_album(album_id)

    album_songs = db.get_album_songs(album_id)
    for album_song in album_songs:
        db.delete_album_song(album_song['id'])
        song_id = album_song['song_id']
        delete_song(song_id)

    db.delete_album(album_id)
    db.delete_file(album['image_file_id'])
    db.add_deleted_album(user_id, album_id)

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

    db_user_album_artists = db.get_user_album_artists(user['id'], after_time)
    metadata['album_artists'] = db_user_album_artists

    #db_playlists = db.get_user_playlists(user['id'], after_time)
    #metadata['playlists'] = db_playlists

    #db_playlist_songs = db.get_user_playlist_songs(user['id'], after_time)
    #metadata['playlist_songs'] = db_playlist_songs

    #db_playlist_images = db.get_user_playlist_images(user['id'], after_time)
    #metadata['playlist_images'] = db_playlist_images

    #db_playlist_removals = db.get_user_playlist_removals(user['id'], after_time)
    #metadata['playlist_removals'] = db_playlist_removals

    db_liked_songs = db.get_user_liked_songs(user['id'], after_time)
    liked_songs = []
    for db_liked_song in db_liked_songs:
        liked_song = {}
        liked_song['song_id'] = db_liked_song['song_id']
        liked_song['id'] = db_liked_song['id']
        liked_song['time_added'] = db_liked_song['time_added']
        liked_songs.append(liked_song)
    metadata['liked_songs'] = liked_songs

    db_liked_song_removals = db.get_user_liked_song_removals(user['id'], after_time)
    metadata['liked_song_removals'] = db_liked_song_removals

    db_playlist_song_additions = db.get_playlist_song_additions(user['id'], after_time)
    metadata['playlist_song_additions'] = db_playlist_song_additions

    db_playlist_song_removals = db.get_playlist_song_removals(user['id'], after_time)
    metadata['playlist_song_removals'] = db_playlist_song_removals

    if after_time is not None:
        metadata['deleted_albums'] = db.get_user_deleted_albums(user['id'], after_time)
#
    #if after_time is not None:
        #metadata['deleted_singles'] = db.get_user_deleted_singles(user['id'], after_time)

    return metadata

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

    artist_id = db.add_artist(artist_name)
    return {'success': True, 'data': {'id': artist_id}}

@bp.route('/add_album', methods=('POST',))
def add_album_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    album_name = request.args.get('album_name')
    year = request.args.get('year')
    album_image_file = None
    artist_ids = []

    if album_name is None:
        return {'success': False, 'error': 'no album_name provided'}
    if year is None:
        return {'success': False, 'error': 'year wasn\'t provided'}
    try:
        year = int(year)
    except ValueError as e:
        return {'success': False, 'error': 'year should be an integer'}

    artist_ids_str = request.args.get('artist_ids')
    if artist_ids_str is None:
        return {'success': False, 'error': 'artist_ids not provided'}

    for artist_id_str in artist_ids_str.split(','):
        try:
            artist_ids.append(int(artist_id_str.strip()))
        except ValueError as e:
            return {'success': False, 'error': 'artist_ids should be a list of comma seperated integers'}

    if 'image' not in request.files:
        return {'success': False, 'error': 'no image provided'}
    else:
        album_image_file = request.files['image']

    for artist_id in artist_ids:
        artist = db.get_artist(artist_id)
        if artist is None:
            return {'success': False, 'error': 'no artist with id {}'.format(artist_id)}

    image_file_id = db.add_file(album_image_file)
    album_id = db.add_album(user['id'], album_name, year, image_file_id)

    for artist_id in artist_ids:
        db.add_album_artist(album_id, artist_id)

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
    if song_name == '':
        return {'success': False, 'error': 'song name cannot be an empty string'}

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

    audio_file_id = db.add_file(song_audio_file)
    format_data = get_audio_stream_format_data(audio_file_id)

    audio_duration = format_data['duration']
    audio_bitrate = format_data['bit_rate']
    audio_codec = format_data['format_name']

    song_id = db.add_song(song_name, audio_file_id, audio_duration,
                          audio_bitrate, audio_codec)

    for artist_id in artist_ids:
        db.add_song_artist(song_id, artist_id)

    db.add_album_song(song_id, album_id, index_in_album)

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

    year = request.args.get('year')
    if year is None:
        return {'success': False, 'error': 'year wasn\'t provided'}
    try:
        year = int(year)
    except ValueError as e:
        return {'success': False, 'error': 'year should be an integer'}

    song_name = request.args.get('name')
    if song_name is None:
        return {'success': False, 'error': 'song\'s name wasnt provided'}
    if song_name == '':
        return {'success': False, 'error': 'song_name cannot be an empty string'}

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

    audio_file_id = db.add_file(song_audio_file)
    image_file_id = db.add_file(song_image_file)
    format_data = get_audio_stream_format_data(audio_file_id)

    audio_duration = format_data['duration']
    audio_bitrate = format_data['bit_rate']
    audio_codec = format_data['format_name']

    song_id = db.add_song(song_name, audio_file_id, audio_duration,
                          audio_bitrate, audio_codec)

    single_song_id = db.add_single_song(user['id'], song_id, image_file_id, year)
    for artist_id in artist_ids:
        db.add_song_artist(song_id, artist_id)

    return {'success': True, 'data': {'id': song_id}}

@bp.route('/unlike_song', methods=('POST',))
def unlike_song_route():
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

    liked_songs_row_id = db.add_liked_song_removal(song_id)
    return {'success': True, 'data': {'liked_songs_row_id': liked_songs_row_id}}

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

@bp.route('/delete_album', methods=('POST',))
def delete_album_route():
    user, error_message = check_auth(request.form,
                                     request_method=request.method,
                                     allow_anonymous=False)
    if error_message:
        return {'success': False, 'error': error_message}

    album_id = request.args.get('id')
    if album_id is None:
        return {'success': False, 'error': 'album_id wasnt provided'}

    if db.get_album(album_id) is None:
        return {'success': False, 'error': 'no album with such id'}

    delete_album(user['id'], album_id)
    return {'success': True, 'data': {}}

@bp.route('/artists', methods=('GET',))
def artists_route():
    artists = db.get_artists()
    return {'success': True, 'data': {'artists': artists}}
