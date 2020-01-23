import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

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


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def insert_song(owner_id, name, artist, album, user_static_file_id,
                duration, lyrics):
    db = get_db()
    db.execute(
        'INSERT INTO songs (owner_id, name, artist, album, lyrics)
         VALUES (?, ?, ?, ?, ?)',
        (owner_id, name, artist, album, lyrics,)
    )
    song_id = db.lastrowid
    db.execute(
        'INSERT INTO song_audio (song_id, user_static_file_id, duration)
         VALUES (?, ?, ?)',
        (song_id, user_static_file_id, duration,)
    )
    db.commit()
    return song_id

def insert_user_static_file(owner_id, add_timestamp, file_path,
                            original_file_name, owner_comment):
    db.execute(
        'INSERT INTO user_static_files (owner_id, add_timestamp, file_path,
                                        original_file_name, owner_comment)
         VALUES (?, ?, ?, ?, ?)',
        (owner_id, add_timestamp, file_path, original_file_name, owner_comment,)
    )
    db.commit()
    return db.lastrowid

def ():
    db.execute(
        'SELECT '
    )
