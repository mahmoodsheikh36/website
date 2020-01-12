import functools
from flask import current_app as app
from flask import send_from_directory
from flask import (
    Blueprint
)
from website.db import get_music_db

import os
import sqlite3
import json

bp = Blueprint('music', __name__, url_prefix='/music')

def get_songs():
    db = get_music_db()
    db_songs = db.execute('SELECT * FROM songs').fetchall()
    return db_songs

def get_song(id):
    db = get_music_db()
    db_song = db.execute('SELECT * FROM songs WHERE id = ?', (id,)).fetchone()
    return db_song

@bp.route('/all_songs', methods=['GET'])
def all_songs():
    db_songs = get_songs()
    songs = []
    for db_song in db_songs:
        song = {}
        song['id'] = db_song['id']
        song['name'] = db_song['name']
        song['artist'] = db_song['artist']
        song['album'] = db_song['album']
        songs.append(song)

    return json.dumps(songs)

@bp.route('/get_song_audio_file/<int:song_id>', methods=['GET'])
def song_audio_file(song_id):
    song = get_song(song_id)
    return send_from_directory(os.path.join(app.instance_path, 'audio'),
                               os.path.basename(song['file_path']))
