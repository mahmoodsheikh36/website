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

@bp.route('metadata')
def metadata_route():
    user, error_message = check_auth(request.form,
                                     request_method=request.method,
                                     allow_anonymous=True)
    if error_message:
        return error_message

    after_time = request.args.get('after_time')
    
    metadata = {}
    db_albums = db.get_user_albums(user['id'], after_time)
    albums = []
    for db_album in db_albums:
        album = {}
        album['id'] = db_album['id']
        album['name'] = db_album['name']
        album['artist_id'] = db_album['artist_id']
        album['timed_added'] = db_album['time_added']
        albums.append(album)
    metadata['albums'] = albums

    db_artists = db.get_user_artists(user['id'], after_time)
    metadata['artists'] = db_artists

    db_songs = db.get_user_songs(user['id'], after_time)
    songs = []
    for db_song in db_songs:
        song = {}
        song['id'] = db_song['id']
        song['name'] = db_song['name']
        song['lyrics'] = db_song['lyrics']
        song['time_added'] = db_song['time_added']
        songs.append(song)
    metadata['songs'] = songs

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
    playlists = []
    for db_playlist in db_playlists:
        playlist = {}
        playlist['id'] = db_playlist['id']
        playlist['name'] = db_playlist['name']
        playlist['time_added'] = db_playlist['time_added']
        playlists.append(playlist)
    metadata['playlists'] = playlists

    db_playlist_songs = db.get_user_playlist_songs(user['id'], after_time)
    metadata['playlist_songs'] = db_playlist_songs

    db_playlist_images = db.get_user_playlist_images(user['id'], after_time)
    metadata['playlist_images'] = db_playlist_images

    return Response(json.dumps(metadata), mimetype='application/json')

@bp.route('/create_playlist', methods=('POST',))
def create_playlist_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)

    if error:
        return error

    playlist_name = request.args.get('name')
    if playlist_name is None:
        return 'please provide the playlists name'

    image_file = None
    original_image_file_name = None
    image_comment = None
    if 'image' in request.files:
        image_file = request.files['image']
    else:
        return 'please provide an image for the playlist'
    if 'image_file_name' in request.form:
        original_image_file_name = request.form['image_file_name']
    if 'image_comment' in request.form:
        image_comment = request.form['image_comment']

    print(original_image_file_name)

    image_file_id = db.add_user_static_file(
            user['id'],
            image_file,
            image_comment,
            original_image_file_name)
    playlist_id = db.add_playlist(user['id'], playlist_name)
    db.add_playlist_image(playlist_id, image_file_id)

    return 'OK, added playlist {}'.format(original_image_file_name)

@bp.route('/add_song_to_playlist', methods=('POST',))
def add_song_to_playlist_route():
    user, error = check_auth(request.form,
                             request_method=request.method,
                             allow_anonymous=False)

    if error:
        return error

    playlist_id = request.args.get('playlist_id')
    if playlist_id is None:
        return 'please provide the playlists id'
    song_id = request.args.get('song_id')
    if song_id is None:
        return 'please provide the songs id that u want add to the playlist'

    db.add_playlist_song(song_id, playlist_id)

    return 'OK'

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

@bp.route('/artists', methods=('POST',))
def artists_route():
    return ''

@bp.route('/add_single_song', methods=('POST',))
def add_single_route():
    username = None
    password = None
    audio_file = None
    song_name = None
    artists_str = None
    audio_duration = None
    song_lyrics = None
    audio_comment = None
    image_comment = None
    image_file = None
    image_original_file_name = None
    audio_original_file_name = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']
    if 'audio' in request.files:
        audio_file = request.files['audio']
    if 'name' in request.form:
        song_name = request.form['name']
    if 'artist' in request.form:
        artists_str = request.form['artist']
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
    if 'audio_file_name' in request.form:
        audio_original_file_name = request.form['audio_file_name']
    if 'image_file_name' in request.form:
        image_original_file_name = request.form['image_file_name']

    error = None

    if not username:
        error = 'huh? wheres the username?'
    if not password:
        error = '-_- u need a password'
    if not audio_file:
        error = 'provide an audio file goddamit!'
    if not song_name:
        error = 'you did not provide the songs name'
    if not artists_str:
        error = 'you did not provide the songs artist names'
    if not audio_duration:
        error = 'you did not provide the songs audio duration'
    if not image_file:
        error = 'you did not provide an image file'

    if error:
        return error

    user = auth.get_user_by_credentials(username, password)
    if user is None:
        return 'wrong credentials'

    artist_names = [artist.strip() for artist in artists_str.split('&')]

    song_id = db.add_song(user['id'], song_name, song_lyrics)
    db.add_single_song(song_id)

    for artist_name in artist_names:
        artist = db.get_artist_by_name(artist_name)
        artist_id = None
        if artist is not None:
            artist_id = artist['id']
        else:
            artist_id = db.add_artist(artist_name)
        db.add_song_artist(song_id, artist_id)

    audio_file_id = db.add_user_static_file(user['id'], audio_file, audio_comment, audio_original_file_name)
    image_file_id = db.add_user_static_file(user['id'], image_file, image_comment, image_original_file_name)
    db.add_song_audio(song_id, audio_file_id, audio_duration)
    db.add_song_image(song_id, image_file_id)

    return 'OK {}, added single song \'{}\' by \'{}\''.format(
                user['username'],
                song_name,
                artist_names[0]
            )

@bp.route('/add_album_song', methods=('POST',))
def add_album_song():
    username = None
    password = None
    audio_file = None
    song_name = None
    album_artist_name = None
    album_name = None
    audio_duration = None
    song_lyrics = None
    audio_comment = None
    image_comment = None
    image_file = None
    artists_str = None
    image_original_file_name = None
    audio_original_file_name = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']
    if 'audio' in request.files:
        audio_file = request.files['audio']
    if 'name' in request.form:
        song_name = request.form['name']
    if 'album_artist' in request.form:
        album_artist_name = request.form['album_artist']
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
    if 'album' in request.form:
        album_name = request.form['album']
    if 'artist' in request.form:
        artists_str = request.form['artist']
    if 'audio_file_name' in request.form:
        audio_original_file_name = request.form['audio_file_name']
    if 'image_file_name' in request.form:
        image_original_file_name = request.form['image_file_name']

    error = None

    if not username:
        error = 'huh? wheres the username?'
    if not password:
        error = '-_- u need a password'
    if not audio_file:
        error = 'provide an audio file goddamit!'
    if not song_name:
        error = 'you did not provide the songs name'
    if not album_artist_name:
        error = 'you did not provide the albums artist name'
    if not audio_duration:
        error = 'you did not provide the songs audio duration'
    if not album_name:
        error = 'you did not provide the albums name'
    if not artists_str:
        error = 'you did not provide the artists'

    if error:
        return error

    user = auth.get_user_by_credentials(username, password)
    if user is None:
        return 'wrong credentials'

    artist_names = [artist.strip() for artist in artists_str.split('&')]

    song_id = db.add_song(user['id'], song_name, song_lyrics)

    album_artist = db.get_artist_by_name(album_artist_name)
    if not album_artist:
        if not image_file:
            return 'you did not provide an image file'
        album_artist_id = db.add_artist(album_artist_name)
    else:
        album_artist_id = album_artist['id']

    for artist_name in artist_names:
        artist = db.get_artist_by_name(album_artist_name)
        artist_id = None
        if artist is not None:
            artist_id = artist['id']
        else:
            artist_id = db.add_artist(album_artist_name)
        song_artists_row_id = db.add_song_artist(song_id, artist_id)

    album = db.get_album(user['id'], album_name, album_artist_id)
    album_id = None
    if album is None:
        if not image_file:
            return 'you did not provide an image file'
        album_id = db.add_album(user['id'], album_name, album_artist_id)
    else:
        album_id = album['id']

    album_songs_row_id = db.add_album_song(song_id, album_id)
    audio_file_id = db.add_user_static_file(
            user['id'],
            audio_file,
            audio_comment,
            audio_original_file_name)

    image_file_msg = ''

    album_image_file = db.get_album_image_file(album_id)
    song_image_id = None
    if image_file and not album_image_file:
        image_file_id = db.add_user_static_file(
                user['id'],
                image_file,
                image_comment,
                image_original_file_name)
        db.add_album_image(album_id, image_file_id)
        song_image_id = db.add_song_image(song_id, image_file_id)
    else:
        song_image_id = db.add_song_image(song_id, album_image_file['user_static_file_id'])
        image_file_msg = 'rejected image, already got one for this album\n'

    db.add_song_audio(song_id, audio_file_id, audio_duration)

    return image_file_msg + 'OK {}, added song \'{}\''.format(user['username'], song_name)

@bp.route('/add_album', methods=('POST',))
def add_album_route():
    username = None
    password = None
    songs_str = None
    songs = None
    album_artist = None
    album_name = None
    album_image_file = None

    if 'username' in request.form:
        username = request.form['username']
    if 'password' in request.form:
        password = request.form['password']
    if 'songs' in request.form:
        songs_str = request.form['songs']
    if 'artist' in request.form:
        album_artist = request.form['artist']
    if 'name' in request.form:
        album_name = request.form['name']
    if 'image' in request.files:
        album_image_file = request.files['image']

    if not username:
        error = 'huh? wheres the username?'
    if not password:
        error = '-_- u need a password'
    if not songs_str:
        error = 'you didn\'t provide songs'
    if not album_artist:
        error = 'you didn\'t provide the artist name'
    if not album_name:
        error = 'you didn\'t provide the album name'

    try:
        songs = json.loads(songs_str)
        if not isinstance(songs, list):
            raise Exception()
    except:
        return 'please provide songs in the correct format'

    user = auth.get_user_by_credentials(username, password)
    if user is None:
        return 'wrong credentials'

    response_text = ''

    artist = db.get_artist_by_name(album_artist)
    artist_id = None
    if artist is None:
        artist_id = db.add_artist(album_artist)
    else:
        artist_id = artist['id']

    album_image_file_id = add_user_static_file(user['id'], album_image_file, None)

    # but if the artist doesn't already exist.. then the album also doesn't exist
    album = db.get_album(album_name, artist_id)
    album_id = None
    if album is None:
        album_id = db.add_album(user['id'], album_name, artist_id)
    else:
        album_id = album['id']

    for song in songs:
        song_name = None
        audio_duration = None
        song_lyrics = None
        audio_comment = None
        audio_file_name = None
        audio_file = None

        if 'name' in song:
            song_name = song['name']
        if 'duration' in song:
            audio_duration = song['duration']
        if 'lyrics' in song:
            song_lyrics = song['lyrics']
        if 'audio_comment' in song:
            comment = song['audio_comment']
        if 'audio_file_name' in song:
            audio_file_name = song['audio_file_name']

        error = None

        if not song_name:
            error = 'you did not provide a songs name'
        elif not audio_duration:
            error = 'you did not provide a songs audio duration'
        elif not audio_file_name:
            error = 'you did not provide the image file name for song {}'.format(song_name)

        if error:
            return error
        
        if not audio_file_name in request.files:
            return 'you did not provide the audio file {}'.format(audio_file_name)

        audio_file = request.files[audio_file_name]

        song_id = db.add_song(user['id'], song_name, song_lyrics)
        db.add_album_song(song_id, artist_id)

        audio_file_id = db.add_user_static_file(user['id'], audio_file, audio_comment)
        db.add_song_audio(song_id, audio_file_id, audio_duration)
        db.add_song_image(song_id, album_image_file_id)

        response_text += 'added song \'{}\'\n'.format(song_name)

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
