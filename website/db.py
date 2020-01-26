import sqlite3

import click
import os, errno
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug import secure_filename

from website.utils import random_str
from website.utils import current_time

def get_static_user_files_dir():
    return os.path.join(current_app.instance_path, 'static_files/')

def get_user_by_id(user_id):
    user = get_db().execute(
        'SELECT * FROM user WHERE id = ?', (user_id,)
    ).fetchone()
    return user

def get_user_by_username(username):
    user = get_db().execute(
        'SELECT * FROM user WHERE username = ?', (username,)
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

    if not os.path.exists(get_static_user_files_dir()):
        try:
            os.makedirs(get_static_user_files_dir())
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

def add_song(owner_id, name, artist, album, audio_file_id, image_file_id,
             duration, lyrics):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO songs (owner_id, name, artist, album, lyrics)\
         VALUES (?, ?, ?, ?, ?)',
        (owner_id, name, artist, album, lyrics,)
    )
    song_id = db_cursor.lastrowid
    db_cursor.execute(
        'INSERT INTO song_audio (song_id, user_static_file_id, duration)\
         VALUES (?, ?, ?)',
        (song_id, audio_file_id, duration,)
    )
    db_cursor.execute(
        'INSERT INTO song_images (song_id, user_static_file_id)\
         VALUES (?, ?)',
        (song_id, audio_file_id)
    )
    db.commit()
    return song_id

def add_user_static_file(owner_id, flask_file, owner_comment):
    on_disk_file_name = random_str()
    flask_file.save(os.path.join(get_static_user_files_dir(), on_disk_file_name))
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO user_static_files (owner_id,\
                                        add_timestamp,\
                                        file_name,\
                                        original_file_name,\
                                        owner_comment)\
         VALUES (?, ?, ?, ?, ?)',
        (owner_id,
         current_time(),
         on_disk_file_name,
         secure_filename(flask_file.name),
         owner_comment)
    )
    db.commit()
    return db_cursor.lastrowid

def get_user_songs(owner_id):
    db = get_db()
    db_cursor = db.cursor()
    songs = db_cursor.execute(
        'SELECT * FROM songs'
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
        elif audio_file['add_timestamp'] < first_audio_file['add_timestamp']:
            audio_file = first_audio_file

    return first_audio_file

def get_song_last_audio(song_id):
    db = get_db()
    db_cursor = db.cursor()
    last_song_audio = db_cursor.execute(
        'SELECT song_audio.* FROM song_audio JOIN user_static_files ON user_static_files.id = song_audio.user_static_file_id AND song_audio.id = ? ORDER BY user_static_files.add_timestamp',
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
        elif audio_file['add_timestamp'] > last_audio_file['add_timestamp']:
            audio_file = last_audio_file

    return last_audio_file

def get_song_last_audio_file_path(song_id):
    audio_file = get_song_last_audio_file(song_id)
    if audio_file is None:
        return None
    return os.path.join(get_static_user_files_dir(), audio_file['file_name'])

def get_song_last_image(song_id):
    db = get_db()
    db_cursor = db.cursor()
    last_song_image = db_cursor.execute(
        'SELECT song_images.* FROM song_images JOIN user_static_files ON user_static_files.id = song_images.user_static_file_id AND song_images.id = ? ORDER BY user_static_files.add_timestamp',
        (song_id,)
    ).fetchone()
    return last_song_image

def get_song_last_image_file_path(song_id):
    song_last_image = get_song_last_image(song_id)
    song_last_image_file = get_user_static_file(song_last_image['user_static_file_id'])
    return os.path.join(get_static_user_files_dir(), song_last_image_file['file_name'])

def get_user_static_file(static_file_id):
    db = get_db()
    db_cursor = db.cursor()
    user_static_file = db_cursor.execute(
        'SELECT * FROM user_static_files WHERE id = ?',
        (static_file_id,)
    ).fetchone()
    return user_static_file
