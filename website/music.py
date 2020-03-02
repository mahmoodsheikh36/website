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

def delete_song(song_id):
    db.delete_song(song_id)
    if db.is_song_liked(song_id):
        db.add_liked_song_removal(song_id)
    for song_image in db.get_song_images(song_id):
        db.delete_user_file(song_image['user_static_file_id'])
        db.delete_song_image(song_image['id'])
    for song_audio_row in db.get_song_audio(song_id):
        db.delete_user_file(song_audio_row['user_static_file_id'])
        db.delete_song_audio(song_audio_row['id'])
    for song_artist_row in db.get_song_artists(song_id):
        db.delete_song_artist_by_row_id(song_artist_row['id'])
    for song_lyrics_row in db.get_song_lyrics(song_id):
        db.delete_song_lyrics(song_lyrics_row['id'])

def delete_single(user_id, single_id):
    db_single = db.get_single(single_id)
    song_id = db_single['song_id']
    delete_song(song_id)
    db.delete_single(single_id)
    db.add_deleted_single(user_id, single_id)

def delete_album(user_id, album_id):
    album_songs = db.get_album_songs(album_id)
    for album_song in album_songs:
        db.delete_album_song(album_song['id'])
        song_id = album_song['song_id']
        delete_song(song_id)

    db.delete_album(album_id)
    album_image = db.get_album_image(album_id)
    db.delete_album_image(album_image['id'])
    db.delete_user_file(album_image['user_static_file_id'])
    db.add_deleted_album(user_id, album_id)

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

@bp.route('/delete_single', methods=('POST',))
def delete_single_route():
    user, error_message = check_auth(request.form,
                                     request_method=request.method,
                                     allow_anonymous=False)
    if error_message:
        return {'success': False, 'error': error_message}

    single_id = request.args.get('id')
    if single_id is None:
        return {'success': False, 'error': 'single_id wasnt provided'}

    if db.get_single(single_id) is None:
        return {'success': False, 'error': 'no single with id: {}'.format(single_id)}

    delete_single(user['id'], single_id)
    return {'success': True, 'data': {}}

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

    if after_time is not None:
        metadata['deleted_singles'] = db.get_user_deleted_singles(user['id'], after_time)

    return metadata

@bp.route('/add_playlist', methods=('POST',))
def add_playlist_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

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
    year = request.args.get('year')
    album_image_file = None
    cue_file = None
    log_file = None

    if album_name is None:
        return {'success': False, 'error': 'no album_name provided'}
    if artist_id is None:
        return {'success': False, 'error': 'no artist_id provided'}
    if year is None:
        return {'success': False, 'error': 'year wasn\'t provided'}
    try:
        year = int(year)
    except ValueError as e:
        return {'success': False, 'error': 'year should be an integer'}

    if 'image' not in request.files:
        return {'success': False, 'error': 'no image provided'}
    else:
        album_image_file = request.files['image']
    
    if 'cue' in request.files:
        cue_file = request.files['cue']

    if 'log' in request.files:
        log_file = request.files['log']

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

    cue_file_id = None
    log_file_id = None
    if cue_file is not None:
        cue_file_id = db.add_user_static_file(
                user['id'],
                cue_file,
                None,
                None)
    if log_file is not None:
        log_file_id = db.add_user_static_file(
                user['id'],
                log_file,
                None,
                None)
    album_id = db.add_album(user['id'], album_name, artist_id, year, cue_file_id, log_file_id)
    album_image_file_id = db.add_user_static_file(
            user['id'],
            album_image_file,
            None,
            None)
    db.add_album_image(album_id, album_image_file_id)

    return {'success': True, 'data': {'album_id': album_id}}

@bp.route('/add_existing_song_to_album', methods=('POST',))
def add_existing_song_to_album_route():
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

    index_in_album = request.args.get('index_in_album')
    if index_in_album is None:
        return {'success': False, 'error': 'song index in album wasnt provided'}
    try:
        index_in_album = int(index_in_album)
    except ValueError as e:
        return {'success': False, 'error': 'index_in_album should be an integer'}

    if db.get_album_song_by_index(album_id, index_in_album) is not None:
        return {'success': False, 'error': 'a song with this index already exists in this album'}

    song_id = request.args.get('song_id')
    if song_id is None:
        return {'success': False, 'error': 'song_id wasnt provided'}
    try:
        song_id = int(song_id)
    except ValueError as e:
        return {'success': False, 'error': 'song_id should be an integer'}

    db.add_album_song(song_id, album_id, index_in_album)

    return {'success': True, 'data': {}}

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

    song_id = db.add_song(user['id'], song_name)
    audio_file_id = db.add_user_static_file(
            user['id'],
            song_audio_file,
            None,
            None)
    db.add_song_audio(song_id, audio_file_id, audio_duration, audio_bitrate)
    for artist_id in artist_ids:
        db.add_song_artist(song_id, artist_id)
    db.add_album_song(song_id, album_id, index_in_album)
    db.add_song_image(song_id, db.get_album_image(album_id)['user_static_file_id'])

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

    song_id = db.add_song(user['id'], song_name)
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
    single_song_id = db.add_single_song(song_id, year)
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

@bp.route('/add_audio_to_song', methods=('POST',))
def add_audio_to_song_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    song_id = None
    if 'song_id' in request.form:
        song_id = request.form['song_id']
    else:
        return {'success': False, 'error': 'song_id wasnt provided'}
    try:
        song_id = int(song_id)
    except ValueError as e:
        return {'success': False, 'error': 'song_id must be an integer'}

    audio_file = None
    if 'audio' in request.files:
        audio_file = request.files['image']
    else:
        return {'success': False, 'error': 'no audio provided'}

    audio_duration = None
    if 'duration' in request.form:
        audio_duration = request.form['duration']
    else:
        return {'success': False, 'error': 'audio duration wasnt providead'}
    try:
        audio_duration = int(audio_duration)
    except ValueError as e:
        return {'success': False, 'error': 'audio duration must be an integer'}

    audio_bitrate = None
    if 'bitrate' in request.form:
        audio_bitrate = request.form['bitrate']
    else:
        return {'success': False, 'error': 'audio bitrate wasnt providead'}
    try:
        audio_bitrate = int(audio_bitrate)
    except ValueError as e:
        return {'success': False, 'error': 'audio bitrate must be an integer'}

    audio_file_id = db.add_user_static_file(
            user['id'],
            audio_file,
            None,
            None)
    db.add_song_audio(song_id, audio_file_id, audio_duration, audio_bitrate)

    return {'success': True, 'data': {}}

@bp.route('/edit_album_artist', methods=('POST',))
def edit_album_artist_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    album_id = None
    if 'album_id' in request.form:
        album_id = request.form['album_id']
    else:
        return {'success': False, 'error': 'no album_id provided'}
    try:
        album_id = int(album_id)
    except ValueError as e:
        return {'success': False, 'error': 'album_id should be an integer'}

    artist_id = None
    if 'artist_id' in request.form:
        artist_id = request.form['artist_id']
    else:
        return {'success': False, 'error': 'no artist_id provided'}
    try:
        artist_id = int(artist_id)
    except ValueError as e:
        return {'success': False, 'error': 'artist_id should be an integer'}

    album = db.get_album(album_id)
    if album is None:
        return {'success': False, 'error': 'no album with such id'}

    aritst = db.get_artist(artist_id)
    if artist is None:
        return {'success': False, 'error': 'no artist with such id'}

    old_artist_id = album['artist_id']
    album_artist_edit_id = add_album_artist_edit(user['id'], album_id, old_artist_id, artist_id)
    db.update_album_artist_id(album_id, artist_id)
    return {'success': True, 'data': {'album_artist_edit_id': album_artist_edit_id}}

@bp.route('/edit_song_artist', methods=('POST',))
def edit_song_artist_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)
    if error:
        return {'success': False, 'error': error}

    song_id = None
    if 'song_id' in request.form:
        song_id = request.form['song_id']
    else:
        return {'success': False, 'error': 'no song_id provided'}
    try:
        song_id = int(song_id)
    except ValueError as e:
        return {'success': False, 'error': 'song_id should be an integer'}

    new_artist_id = None
    if 'new_artist_id' in request.form:
        new_artist_id = request.form['new_artist_id']
    else:
        return {'success': False, 'error': 'no new_artist_id provided'}
    try:
        new_artist_id = int(new_artist_id)
    except ValueError as e:
        return {'success': False, 'error': 'new_artist_id should be an integer'}

    old_artist_id = None
    if 'old_artist_id' in request.form:
        old_artist_id = request.form['old_artist_id']
    else:
        return {'success': False, 'error': 'no old_artist_id provided'}
    try:
        old_artist_id = int(old_artist_id)
    except ValueError as e:
        return {'success': False, 'error': 'old_artist_id should be an integer'}

    song = db.get_song(song_id)
    if song is None:
        return {'success': False, 'error': 'no song with such id'}
    
    old_artist = db.get_artist(old_artist_id)
    if old_artist is None:
        return {'success': False, 'error': 'no artist with such id {}'.format(old_artist_id)}

    new_artist = db.get_artist(new_artist_id)
    if new_artist is None:
        return {'success': False, 'error': 'no artist with such id {}'.format(new_artist_id)}

    db.add_song_artist_edit(user['id'], song_id, old_artist_id, new_artist_id)
    db.delete_song_artist(song_id, new_artist_id)
    db.add_song_artist(song_id, new_artist_id)
    return {'success': True, 'data': {}}

@bp.route('/artists', methods=('GET',))
def get_artists_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=True)
    if error:
        return {'success': False, 'error': error}

    db_artists = db.get_user_artists(user['id'])
    return {'success': True, 'data': {'artists': db_artists}}

@bp.route('/albums', methods=('GET',))
def get_albums_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=True)
    if error:
        return {'success': False, 'error': error}

    db_albums = db.get_user_albums(user['id'])
    return {'success': True, 'data': {'albums': db_albums}}
