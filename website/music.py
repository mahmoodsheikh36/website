import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from website.db import get_music_db

import sqlite3
import json

bp = Blueprint('music', __name__, url_prefix='/music')

def get_songs():
    db = get_music_db()
    db_songs = db.execute('SELECT * FROM songs').fetchall()
    return db_songs

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
