import sqlite3
from flask import current_app
import json
from os.path import expanduser
from website.db import get_spotify_db

def get_tracks():
    db = get_spotify_db()
    db_tracks = db.execute('SELECT * FROM Tracks').fetchall()
    tracks = []
    for db_track in db_tracks:
        tracks.append(parse_db_track(db_track))
    sort_tracks(tracks)
    print(tracks[0]["listen_time"])
    return tracks

def sort_tracks(tracks):
    tracks_len = len(tracks)
    for i in range(tracks_len):
        for j in range(i + 1, tracks_len):
            if tracks[i]['listen_time'] < tracks[j]['listen_time']:
                tracks[i], tracks[j] = tracks[j], tracks[i]

def parse_db_track(track):
    parsed_track = {}

    artists = json.loads(track["artists"])
    album = json.loads(track["album"])
    parsed_track["artist"] = artists[0]["name"]
    parsed_track["listen_time"] = round(track["playtime"])
    parsed_track["album"] = album["name"]
    parsed_track["name"] = track["title"]
    parsed_track["image_url"] = album["images"][0]["url"]

    return parsed_track

def get_access_token():
    home = expanduser("~")
    with open(home + '/mydata/spotify_data/access_values.json') as access_file:
        return json.loads(access_file.read())['access_token']
