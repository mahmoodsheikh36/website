import functools
from flask import current_app as app
from flask import (
    Blueprint, Response, request, send_from_directory
)
import os
import sqlite3
import json

from website.db import get_music_db

bp = Blueprint('music', __name__, url_prefix='/music')

def get_songs():
    db = get_music_db()
    db_songs = db.execute('SELECT * FROM songs').fetchall()
    return db_songs
def get_songs_after_id(id):
    db = get_music_db()
    db_songs = db.execute('SELECT * FROM songs WHERE id > ?', (id,)).fetchall()
    return db_songs

def get_song(id):
    db = get_music_db()
    db_song = db.execute('SELECT * FROM songs WHERE id = ?', (id,)).fetchone()
    return db_song

@bp.route('/songs', methods=['GET'])
def all_songs():
    after_id = request.args.get('after_id')
    print("after_id: " + str(after_id))
    if after_id != None:
        try:
            db_songs = get_songs_after_id(int(after_id))
        except ValueError as e:
            return Response('after_id has to be an integer')
    else:
        db_songs = get_songs()
    print('after_id:' + str(after_id))
    songs = []
    for db_song in db_songs:
        song = {}
        song['id'] = db_song['id']
        song['name'] = db_song['name']
        song['artist'] = db_song['artist']
        song['album'] = db_song['album']
        song['duration'] = db_song['duration']
        song['date_added'] = db_song['date_of_entry']
        songs.append(song)

    return Response(json.dumps(songs), mimetype='application/json')

@bp.route('/get_song_audio_file/<int:song_id>', methods=['GET'])
def song_audio_file(song_id):
    song = get_song(song_id)
    return send_from_directory(os.path.join(app.instance_path, 'audio'),
                               os.path.basename(song['audio_file_path']))

@bp.route('/get_song_image_file/<int:song_id>', methods=['GET'])
def song_image_file(song_id):
    song = get_song(song_id)
    return send_from_directory(os.path.join(app.instance_path, 'image'),
                               os.path.basename(song['image_file_path']))
