import sqlite3

import click
import os, errno
from flask import current_app, g
from flask.cli import with_appcontext
from werkzeug.utils import secure_filename

from website.utils import random_str, current_time, get_mimetype_of_flask_file

def get_files_dir():
    return os.path.join(current_app.instance_path, 'files/')

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

def open_db(path=None):
    if path is None:
        path = current_app.config['DATABASE']
    db = sqlite3.connect(
        path,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    db.row_factory = dict_factory
    return db

def get_db():
    if 'db' not in g:
        g.db = open_db()

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    if not os.path.exists(get_files_dir()):
        try:
            os.makedirs(get_files_dir())
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

@click.command('init-db')
@with_appcontext
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)

def add_song(name, audio_file_id, duration, bitrate, codec, sample_rate,
             channels):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO songs (name, audio_file_id, duration, bitrate, codec,\
                            time_added, sample_rate, channels)\
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (name, audio_file_id, duration, bitrate, codec, current_time(),
         sample_rate, channels))
    db.commit()
    return db_cursor.lastrowid

def add_single_song(owner_id, song_id, image_file_id, year):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
      'INSERT INTO single_songs (owner_id, song_id, time_added, image_file_id, year)\
       VALUES (?, ?, ?, ?, ?)', (owner_id, song_id, current_time(), image_file_id, year))
    db.commit()
    return db_cursor.lastrowid

def add_album_song(song_id, album_id, index_in_album):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
      'INSERT INTO album_songs (song_id, album_id, index_in_album, time_added)\
       VALUES (?, ?, ?, ?)', (song_id, album_id, index_in_album, current_time())
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

def add_file(flask_file, original_name=None):
    if original_name is None:
        original_name = flask_file.filename
    filename = random_str()
    db = get_db()
    db_cursor = db.cursor()
    flask_file.save(os.path.join(get_files_dir(), filename))
    mimetype = get_mimetype_of_flask_file(flask_file)
    db_cursor.execute(
        'INSERT INTO files (time_added, original_name, name, mimetype)\
         VALUES (?, ?, ?, ?)',
        (current_time(),
         original_name,
         filename,
         mimetype))
    db.commit()
    return db_cursor.lastrowid

def get_user_songs(owner_id, after_time=None):
    db = get_db()
    db_cursor = db.cursor()
    if after_time is None:
        songs = db_cursor.execute(
            'SELECT * FROM songs WHERE id IN (SELECT song_id FROM single_songs WHERE owner_id = ?) OR id IN (SELECT song_id FROM album_songs WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?))',
            (owner_id, owner_id)
        ).fetchall()
    else:
        songs = db_cursor.execute(
            'SELECT * FROM songs WHERE (id IN (SELECT song_id FROM single_songs WHERE owner_id = ?) OR id IN (SELECT song_id FROM album_songs WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?))) AND time_added > ?',
            (owner_id, owner_id, after_time)
        ).fetchall()
    return songs

def get_file(file_id):
    db = get_db()
    db_cursor = db.cursor()
    return db_cursor.execute(
        'SELECT * FROM files WHERE id = ?',
        (file_id,)
    ).fetchone()

def get_file_path(file_id):
    db_file = get_file(file_id)
    return os.path.join(get_files_dir(), db_file['name'])

def add_artist(name):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
       'INSERT INTO artists (name, time_added)\
        VALUES (?, ?)', (name, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def add_album(owner_id, name, year, image_file_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO albums (owner_id, name, image_file_id, time_added, year)\
         VALUES (?, ?, ?, ?, ?)',
        (owner_id, name, image_file_id, current_time(), year,)
    )
    db.commit()
    return db_cursor.lastrowid

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

def get_single(id):
    db = get_db()
    song = db.execute(
            'SELECT * FROM single_songs WHERE id = ?',
            (id,)
    ).fetchone()
    return song

def get_user_single_songs(owner_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT * FROM single_songs WHERE owner_id = ?',
                (owner_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT * FROM single_songs WHERE owner_id = ? AND time_added > ?',
                (owner_id, after_time,)
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

def get_artists():
    db = get_db()
    return get_db().execute('SELECT * FROM artists').fetchall()

def get_user_artists(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        artists = db.execute(
                'SELECT * FROM artists WHERE id IN (SELECT artist_id FROM song_artists WHERE song_artists.song_id IN (SELECT song_id FROM single_songs WHERE owner_id = ?)) OR artists.id IN (SELECT artist_id FROM album_artists WHERE album_artists.album_id IN (SELECT id FROM albums WHERE owner_id = ?)) OR artists.id IN (SELECT artist_id FROM song_artists WHERE song_id IN (SELECT id FROM songs WHERE id IN (SELECT song_id FROM album_songs)))',
                (user_id, user_id)
        ).fetchall()
    else:
        artists = db.execute(
                'SELECT * FROM artists WHERE (id IN (SELECT artist_id FROM song_artists WHERE song_artists.song_id IN (SELECT song_id FROM single_songs WHERE owner_id = ?)) OR id IN (SELECT artist_id FROM album_artists WHERE album_artists.album_id IN (SELECT id FROM albums WHERE owner_id = ?)) OR artists.id IN (SELECT artist_id FROM song_artists WHERE song_id IN (SELECT id FROM songs WHERE id IN (SELECT song_id FROM album_songs)))) AND time_added > ?',
                (user_id, user_id, after_time)
        ).fetchall()
    return artists

def get_user_song_artists(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        song_artists = db.execute(
                'SELECT * FROM song_artists WHERE song_id IN (SELECT id FROM songs WHERE id IN (SELECT song_id FROM single_songs WHERE owner_id = ?) OR id IN (SELECT song_id FROM album_songs WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?)))',
                (user_id, user_id)
        ).fetchall()
    else:
        song_artists = db.execute(
                'SELECT * FROM song_artists WHERE song_id IN (SELECT id FROM songs WHERE id IN (SELECT song_id FROM single_songs WHERE owner_id = ?) OR id IN (SELECT song_id FROM album_songs WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?))) AND time_added > ?',
                (user_id, user_id, after_time)
        ).fetchall()
    return song_artists

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

def get_user_album_songs(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT * FROM album_songs WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?)',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT * FROM album_songs WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?) AND time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_user_playlists(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT id,name,time_added FROM playlists WHERE owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT id,name,time_added FROM playlists WHERE owner_id = ? AND time_added > ?',
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

def add_playlist_song(playlist_id, song_id):
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

def get_playlist_song(playlist_id, song_id):
    return get_db().execute(
            'SELECT * FROM playlist_songs WHERE playlist_id = ? AND song_id = ?',
            (playlist_id, song_id)
    ).fetchone()

def get_user_playlist_removals(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT playlist_removals.* FROM playlist_removals JOIN playlists ON playlists.id = playlist_removals.playlist_id AND playlists.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT playlist_removals.* FROM playlist_removals JOIN playlists ON playlists.id = playlist_removals.playlist_id AND playlists.owner_id = ? AND playlist_removals.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_user_liked_songs(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT * FROM liked_songs WHERE song_id IN (SELECT song_id FROM albums WHERE owner_id = ?) OR song_id IN (SELECT song_id FROM single_songs WHERE owner_id = ?)',
                (user_id, user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT * FROM liked_songs WHERE (song_id IN (SELECT song_id FROM albums WHERE owner_id = ?) OR song_id IN (SELECT song_id FROM single_songs WHERE owner_id = ?)) AND time_added > ?',
                (user_id, user_id, after_time,)
        ).fetchall()

def get_user_liked_song_removals(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT * FROM liked_song_removals WHERE owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT * FROM liked_song_removals WHERE owner_id = ? AND time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_playlist_song_additions(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT playlist_song_additions.* FROM playlist_song_additions JOIN playlists ON playlists.id = playlist_song_additions.playlist_id AND playlists.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT playlist_song_additions.* FROM playlist_song_additions JOIN playlists ON playlists.id = playlist_song_additions.song_id AND playlists.owner_id = ? AND playlist_song_additions.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_playlist_song_removals(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        return db.execute(
                'SELECT playlist_song_removals.* FROM playlist_song_removals JOIN playlists ON playlists.id = playlist_song_removals.playlist_id AND playlists.owner_id = ?',
                (user_id,)
        ).fetchall()
    else:
        return db.execute(
                'SELECT playlist_song_removals.* FROM playlist_song_removals JOIN playlists ON playlists.id = playlist_song_removals.song_id AND playlists.owner_id = ? AND playlist_song_removals.time_added > ?',
                (user_id, after_time)
        ).fetchall()

def get_album_song_by_index(album_id, index_in_album):
    return get_db().execute(
            'SELECT * FROM album_songs WHERE album_id = ? AND index_in_album = ?',
            (album_id, index_in_album)
    ).fetchone()

def add_liked_song(song_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO liked_songs (song_id, time_added)\
         VALUES (?, ?)',
        (song_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_album(album_id):
    return get_db().execute(
            'SELECT * FROM albums WHERE id = ?',
            (album_id,)
    ).fetchone()

def delete_album(album_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'DELETE FROM albums WHERE id = ?',
        (album_id,)
    )
    db.commit()
    return db_cursor.lastrowid

def delete_single(single_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'DELETE FROM single_songs WHERE id = ?',
        (single_id,)
    )
    db.commit()
    return db_cursor.lastrowid

def delete_album_image(album_image_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'DELETE FROM album_images WHERE id = ?',
        (album_image_id,)
    )
    db.commit()

def delete_file(file_id):
    db = get_db()
    db_cursor = db.cursor()
    db_file = get_file(file_id)
    file_name = db_file['name']
    file_path = os.path.join(get_files_dir(), file_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    db_cursor.execute(
        'DELETE FROM files WHERE id = ?',
        (file_id,)
    )
    db.commit()

def delete_album_song(album_songs_row_id):
    db = get_db()
    db.cursor().execute(
        'DELETE FROM album_songs WHERE id = ?',
        (album_songs_row_id,)
    )
    db.commit()

def delete_song(song_id):
    db = get_db()
    db.cursor().execute(
        'DELETE FROM songs WHERE id = ?',
        (song_id,)
    )
    db.commit()

def add_deleted_album(owner_id, album_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO deleted_albums (owner_id, album_id, time_added)\
         VALUES (?, ?, ?)',
        (owner_id, album_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def add_deleted_single(owner_id, single_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO deleted_single_songs (owner_id, single_id, time_added)\
         VALUES (?, ?, ?)',
        (owner_id, single_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_user_deleted_albums(user_id, after_time):
    db = get_db()
    db_cursor = db.cursor()
    if after_time is None:
        songs = db_cursor.execute(
            'SELECT * FROM deleted_albums WHERE owner_id = ?',
            (user_id,)
        ).fetchall()
    else:
        songs = db_cursor.execute(
            'SELECT * FROM deleted_albums WHERE owner_id = ? AND time_added > ?',
            (user_id, after_time)
        ).fetchall()
    return songs

def get_user_deleted_singles(user_id, after_time):
    db = get_db()
    db_cursor = db.cursor()
    if after_time is None:
        deleted_singles = db_cursor.execute(
            'SELECT single_song_id,time_added FROM deleted_single_songs WHERE owner_id = ?',
            (user_id,)
        ).fetchall()
    else:
        deleted_singles = db_cursor.execute(
            'SELECT single_song_id,time_added FROM deleted_single_songs WHERE owner_id = ? AND time_added > ?',
            (user_id, after_time)
        ).fetchall()
    return deleted_singles

def update_album_artist_id(album_id, new_artist_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'UPDATE albums SET artist_id = ? WHERE id = ?',
        (new_artist_id, album_id)
    )
    db.commit()

def delete_song_artist(song_artist_id):
    db = get_db()
    db_cursor = db.cursor()
    songs = db_cursor.execute(
        'DELETE FROM song_artists WHERE id = ?',
        (song_artist_id,)
    )
    db.commit()

def add_liked_song_removal(song_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO liked_song_removals (song_id, time_added)\
         VALUES (?, ?)',
        (song_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_liked_song(song_id):
    return get_db().execute(
            'SELECT * FROM liked_songs WHERE song_id = ?',
            (song_id,)
    ).fetchone()

def is_song_liked(song_id):
    return get_liked_song(song_id) is not None

def add_image(file_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO images (time_added, file_id)\
         VALUES (?, ?)',
        (current_time(), file_id))
    db.commit()
    return db_cursor.lastrowid

def add_collage(owner_id, title):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO collages (owner_id, title, time_added)\
         VALUES (?, ?, ?)',
        (owner_id, title, current_time()))
    db.commit()
    return db_cursor.lastrowid

def get_image(image_id):
    return get_db().execute(
        'SELECT * FROM images WHERE id = ?', (image_id,)
    ).fetchone()

def get_collage(collage_id):
    return get_db().execute(
        'SELECT * FROM collages WHERE id = ?', (collage_id,)
    ).fetchone()

def add_collage_image(collage_id, image_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO collage_images (collage_id, image_id, time_added)\
         VALUES (?, ?, ?)',
        (collage_id, image_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_collage_images(collage_id):
    return get_db().execute(
            'SELECT DISTINCT images.* FROM images JOIN collage_images ON collage_images.collage_id = ?',
            (collage_id,)
    ).fetchall()
    
def add_album_artist(album_id, artist_id):
    db = get_db()
    db_cursor = db.cursor()
    db_cursor.execute(
        'INSERT INTO album_artists (album_id, artist_id, time_added)\
         VALUES (?, ?, ?)',
        (album_id, artist_id, current_time())
    )
    db.commit()
    return db_cursor.lastrowid

def get_user_album_artists(user_id, after_time=None):
    db = get_db()
    if after_time is None:
        song_artists = db.execute(
                'SELECT * FROM album_artists WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?)',
                (user_id,)
        ).fetchall()
    else:
        song_artists = db.execute(
                'SELECT * FROM album_artists WHERE album_id IN (SELECT id FROM albums WHERE owner_id = ?) AND time_added > ?',
                (user_id, after_time)
        ).fetchall()
    return song_artists

def delete_song_artists(song_id):
    db = get_db()
    db_cursor = db.cursor()
    songs = db_cursor.execute(
        'DELETE FROM song_artists WHERE song_id = ?',
        (song_id,)
    )
    db.commit()
