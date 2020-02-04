import sqlite3

import click
import os, errno
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug import secure_filename

from website.utils import random_str
from website.utils import current_time

def get_user_static_files_dir():
    return os.path.join(current_app.instance_path, 'static_files/')

def get_user(user_id):
    user = get_db().execute(
        'SELECT * FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    return user

def get_user_by_username(username):
    user = get_db().execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    return user

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = dict_factory

    return g.db

def get_music_db():
    if 'music_db' not in g:
        g.music_db = sqlite3.connect(
            current_app.config['MUSIC_DATABASE'],
        )
        g.music_db.row_factory = sqlite3.Row

    return g.music_db

def get_spotify_db():
    if 'spotify_db' not in g:
        g.spotify_db = sqlite3.connect(
            current_app.config['SPOTIFY_DATABASE'],
        )
        g.spotify_db.row_factory = sqlite3.Row

    return g.spotify_db

def close_db(e=None):
    db = g.pop('db', None)
    spotify_db = g.pop('spotify_db', None)
    music_db = g.pop('music_db', None)

    if db is not None:
        db.close()
    if spotify_db is not None:
        spotify_db.close()
    if music_db is not None:
        music_db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    if not os.path.exists(get_user_static_files_dir()):
        try:
            os.makedirs(get_user_static_files_dir())
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def add_song(owner_id, name, lyrics):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO songs (owner_id, name, lyrics, time_added)\
         VALUES (?, ?, ?, ?)',
        (owner_id, name, lyrics, current_time()))
    db.commit()
    return db_cursor.lastrowid

def add_single_song(song_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
      'INSERT INTO single_songs (song_id, time_added)\
       VALUES (?, ?)', (song_id, current_time()))
    db.commit()
    return db_cursor.lastrowid

def add_album_song(song_id, album_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
      'INSERT INTO album_songs (song_id, album_id, time_added)\
       VALUES (?, ?, ?)', (song_id, album_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def add_song_audio(song_id, user_static_file_id, duration):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
      'INSERT INTO song_audio (song_id, user_static_file_id, duration, time_added)\
       VALUES (?, ?, ?, ?)', (song_id, user_static_file_id, duration, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def add_song_image(song_id, image_static_file_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
      'INSERT INTO song_images (song_id, user_static_file_id, time_added)\
       VALUES (?, ?, ?)', (song_id, image_static_file_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def add_album_image(album_id, image_static_file_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
      'INSERT INTO album_images (album_id, user_static_file_id, time_added)\
       VALUES (?, ?, ?)', (album_id, image_static_file_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def add_single(owner_id, name, artist, album, audio_file_id, image_file_id,
                duration, lyrics):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO songs (owner_id, name, artist, album, lyrics, time_added)\
         VALUES (?, ?, ?, ?, ?, ?)',
        (owner_id, name, artist, album, lyrics, current_time())
    )
    song_id = db_cursor.lastrowid
    db_cursor.execute(
        'INSERT INTO song_audio (song_id, user_static_file_id, duration, time_added)\
         VALUES (?, ?, ?, ?)',
        (song_id, audio_file_id, duration, current_time())
    )
    db_cursor.execute(
        'INSERT INTO song_images (song_id, user_static_file_id, time_added)\
         VALUES (?, ?, ?)',
        (song_id, image_file_id, current_time())
    )
    db.commit()
    return song_id

def add_user_static_file(owner_id, flask_file, owner_comment, original_file_name=None):
    if original_file_name is None:
        original_file_name = flask_file.name
    on_disk_file_name = random_str()
    flask_file.save(os.path.join(get_user_static_files_dir(), on_disk_file_name))
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO user_static_files (owner_id,\
                                        time_added,\
                                        file_name,\
                                        original_file_name,\
                                        owner_comment)\
         VALUES (?, ?, ?, ?, ?)',
        (owner_id,
         current_time(),
         on_disk_file_name,
         original_file_name,
         owner_comment)
    )
    db.commit()
    return db_cursor.lastrowid

def get_user_songs(owner_id, after_time=None):
    db = get_db()
    db_cursor = db.cursor()
    if after_time is None:
        songs = db_cursor.execute(
            'SELECT * FROM songs WHERE owner_id = ?', (owner_id,)
        ).fetchall()
    else:
        songs = db_cursor.execute(
            'SELECT * FROM songs WHERE owner_id = ? AND time_added > ?',
            (owner_id, after_time)
        ).fetchall()
    return songs

def get_user_songs_after_id(owner_id, after_id):
    db = get_db()
    db_cursor = db.cursor()
    songs = db_cursor.execute(
        'SELECT * FROM songs WHERE id > ? AND owner_id = ?',
        (after_id, owner_id)
    ).fetchall()
    return songs

# returns an array each containing a song_audio dictionary
def get_all_song_audio(song_id):
    db = get_db()
    db_cursor = db.cursor()
    all_song_audio = db_cursor.execute(
        'SELECT * FROM song_audio WHERE song_id = ?',
        (song_id,)
    ).fetchall()
    return all_song_audio

def get_song_first_audio_file(song_id):
    all_song_audio = get_all_song_audio(song_id)
    db = get_db()
    db_cursor = db.cursor()
    first_audio_file = None
    for song_audio in all_song_audio:
        audio_file = db_cursor.execute(
            'SELECT * FROM user_static_files WHERE id = ?',
            (song_audio['user_static_file_id'],)
        ).fetchone()

        if first_audio_file is None:
            first_audio_file = audio_file
        elif audio_file['time_added'] < first_audio_file['time_added']:
            audio_file = first_audio_file

    return first_audio_file

def get_song_last_audio(song_id):
    db = get_db()
    db_cursor = db.cursor()
    last_song_audio = db_cursor.execute(
        'SELECT song_audio.* FROM song_audio JOIN user_static_files ON user_static_files.id = song_audio.user_static_file_id AND song_audio.id = ? ORDER BY user_static_files.time_added',
        (song_id,)
    ).fetchone()
    return last_song_audio

# this contains duplicate code - the following function is almost same as the previous
def get_song_last_audio_file(song_id):
    all_song_audio = get_all_song_audio(song_id)
    db = get_db()
    db_cursor = db.cursor()
    last_audio_file = None
    for song_audio in all_song_audio:
        audio_file = db_cursor.execute(
            'SELECT * FROM user_static_files WHERE id = ?',
            (song_audio['user_static_file_id'],)
        ).fetchone()

        if last_audio_file is None:
            last_audio_file = audio_file
        elif audio_file['time_added'] > last_audio_file['time_added']:
            audio_file = last_audio_file

    return last_audio_file

def get_song_last_audio_file_path(song_id):
    audio_file = get_song_last_audio_file(song_id)
    if audio_file is None:
        return None
    return os.path.join(get_user_static_files_dir(), audio_file['file_name'])

def get_song_last_image(song_id):
    db = get_db()
    db_cursor = db.cursor()
    last_song_image = db_cursor.execute(
        'SELECT song_images.* FROM song_images JOIN user_static_files ON user_static_files.id = song_images.user_static_file_id AND song_images.id = ? ORDER BY user_static_files.time_added',
        (song_id,)
    ).fetchone()
    return last_song_image

def get_song_last_image_file_path(song_id):
    song_last_image = get_song_last_image(song_id)
    song_last_image_file = get_user_static_file(song_last_image['user_static_file_id'])
    return os.path.join(get_user_static_files_dir(), song_last_image_file['file_name'])

def get_user_static_file(static_file_id):
    db = get_db()
    db_cursor = db.cursor()
    user_static_file = db_cursor.execute(
        'SELECT * FROM user_static_files WHERE id = ?',
        (static_file_id,)
    ).fetchone()
    return user_static_file

def add_artist(name):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
       'INSERT INTO artists (name, time_added)\
        VALUES (?, ?)', (name, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

# this should not be used :( because 2 artists can ofc have the same name
def get_artist_by_name(name):
    db = get_db()
    artist = db.execute('SELECT * FROM artists WHERE name = ?', (name,)).fetchone()
    return artist

def add_album(owner_id, name, artist_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO albums (owner_id, name, artist_id, time_added)\
         VALUES (?, ?, ?, ?)',
        (owner_id, name, artist_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_album(owner_id, album_name, artist_id):
    db = get_db()
    album = db.execute(
        'SELECT * FROM albums WHERE owner_id = ? AND name = ? AND artist_id = ?',
        (owner_id, album_name, artist_id)
    ).fetchone()
    return album

def get_album_image_file(album_id):
    db = get_db()
    album = db.execute(
        'SELECT * FROM album_images WHERE album_id = ?',
        (album_id,)
    ).fetchone()
    return album

def get_user_albums(owner_id, after_time=None):
    db = get_db()
    if after_time is None:
        albums = db.execute(
                'SELECT * FROM albums WHERE owner_id = ?',
                (owner_id,)
        ).fetchall()
    else:
        albums = db.execute(
                'SELECT * FROM albums WHERE owner_id = ? AND time_added > ?',
                (owner_id, after_time)
        ).fetchall()
    return albums

def get_album_songs(album_id):
    db = get_db()
    songs = db.execute(
            'SELECT * FROM album_songs WHERE album_id = ?',
            (album_id,)
    ).fetchall()
    return songs

def get_song(id):
    db = get_db()
    song = db.execute(
            'SELECT * FROM songs WHERE id = ?',
            (id,)
    ).fetchone()
    return song

def get_user_single_songs(owner_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT single_songs.* FROM single_songs JOIN songs on songs.id = single_songs.song_id AND songs.owner_id = ?',
                (owner_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT single_songs.* FROM single_songs JOIN songs on songs.id = single_songs.song_id AND songs.owner_id = ? WHERE single_songs.time_added > ?',
                (owner_id, after_time)
        ).fetchall()

def add_song_artist(song_id, artist_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO song_artists (song_id, artist_id, time_added)\
         VALUES (?, ?, ?)',
        (song_id, artist_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_song_artists(song_id):
    db = get_db()
    song_artists = db.execute(
            'SELECT * FROM song_artists WHERE song_id = ?',
            (song_id,)
    ).fetchall()
    return song_artists

def get_artist(artist_id):
    db = get_db()
    artist = db.execute(
            'SELECT * FROM artists WHERE id = ?',
            (artist_id,)
    ).fetchone()
    return artist

def get_user_artists(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        artists = db.execute(
                'SELECT DISTINCT artists.* FROM artists JOIN song_artists ON song_artists.artist_id = artists.id JOIN songs ON songs.id = song_artists.song_id AND songs.owner_id = ? UNION SELECT artists.* FROM artists JOIN albums ON albums.artist_id = artists.id AND albums.owner_id = ?',
                (user_id, user_id,)
        ).fetchall()
    else:
        artists = db.execute(
                'SELECT DISTINCT artists.* FROM artists JOIN song_artists ON song_artists.artist_id = artists.id JOIN songs ON songs.id = song_artists.song_id AND songs.owner_id = ? UNION SELECT artists.* FROM artists JOIN albums ON albums.artist_id = artists.id AND albums.owner_id = ? AND artists.time_added > ?',
                (user_id, user_id, after_time)
        ).fetchall()
    return artists

def get_user_song_artists(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        song_artists = db.execute(
                'SELECT song_artists.* FROM song_artists JOIN songs ON songs.id = song_artists.song_id AND songs.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        song_artists = db.execute(
                'SELECT song_artists.* FROM song_artists JOIN songs ON songs.id = song_artists.song_id AND songs.owner_id = ? AND song_artists.time_added > ?',
                (user_id, after_time)
        ).fetchall()
    return song_artists

def get_user_song_images(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        song_images = db.execute(
                'SELECT song_images.* FROM song_images JOIN songs ON songs.id = song_images.song_id AND songs.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        song_images = db.execute(
                'SELECT song_images.* FROM song_images JOIN songs ON songs.id = song_images.song_id AND songs.owner_id = ? AND song_images.time_added > ?',
                (user_id, after_time)
        ).fetchall()
    return song_images

def get_user_album_images(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT album_images.* FROM album_images JOIN albums ON albums.id = album_images.album_id AND albums.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT album_images.* FROM album_images JOIN albums ON albums.id = album_images.album_id AND albums.owner_id = ? AND album_images.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_user_song_audio(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT song_audio.* FROM song_audio JOIN songs ON songs.id = song_audio.song_id AND songs.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT song_audio.* FROM song_audio JOIN songs ON songs.id = song_audio.song_id AND songs.owner_id = ? AND song_audio.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_user_album_songs(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT album_songs.* FROM album_songs JOIN songs ON songs.id = album_songs.song_id AND songs.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT album_songs.* FROM album_songs JOIN songs ON songs.id = album_songs.song_id AND songs.owner_id = ? WHERE album_songs.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_user_playlists(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT * FROM playlists WHERE owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT * FROM playlists WHERE owner_id = ? AND time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_user_playlist_songs(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT playlist_songs.* FROM playlist_songs JOIN playlists ON playlists.id = playlist_songs.playlist_id AND playlists.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT playlist_songs.* FROM playlist_songs JOIN playlists ON playlists.id = playlist_songs.playlist_id AND playlists.owner_id = ? AND playlist_songs.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def add_playlist(user_id, name):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO playlists (name, time_added, owner_id)\
         VALUES (?, ?, ?)',
        (name, current_time(), user_id)
    )
    db.commit()
    return db_cursor.lastrowid

def add_playlist_song(song_id, playlist_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO playlist_songs (song_id, playlist_id, time_added)\
         VALUES (?, ?, ?)',
        (song_id, playlist_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def add_playlist_image(playlist_id, file_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO playlist_images (playlist_id, user_static_file_id, time_added)\
         VALUES (?, ?, ?)',
        (playlist_id, file_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_user_playlist_images(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT playlist_images.* FROM playlist_images JOIN playlists ON playlists.id = playlist_images.playlist_id AND playlists.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT playlist_images.* FROM playlist_images JOIN playlists ON playlists.id = playlist_images.playlist_id AND playlists.owner_id = ? AND playlist_images.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def add_hidden_album(album_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO hidden_albums (album_id, time_added)\
         VALUES (?, ?)',
        (album_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_hidden_album(album_id):
    return get_db().execute(
            'SELECT * FROM hidden_albums WHERE album_id = ?',
            (album_id,)
    ).fetchone()

def is_album_hidden(album_id):
    hidden_album_row = get_hidden_album(album_id)
    return hidden_album_row is not None

def get_hidden_albums(after_time=None):
    if after_time is None:
        return get_db().execute(
                'SELECT * FROM hidden_albums',
        ).fetchall()
    else:
        return get_db().execute(
                'SELECT * FROM hidden_albums WHERE time_added > ?',
                (after_time,)
        ).fetchall()
