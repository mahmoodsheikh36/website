import functools
from flask import (
    Blueprint, render_template
)

from website import db
from website.utils import current_time

from commandify.db import DBProvider
cmdify_db_provider = DBProvider()

bp = Blueprint('music', __name__, url_prefix='/music')

@bp.route('/', methods=('GET',))
def music_index():
    albums, tracks, artists = cmdify_db_provider.get_music()

    for track in tracks:
        ms_listened = track.ms_listened()
        track.secs_listened = (ms_listened // 1000) % 60
        track.mins_listened = (ms_listened // 60000) % 60
        track.hrs_listened = (ms_listened // 360000)

        track.trend = []
        first_listen_time = track.plays[0].time_started
        last_listen_time = track.plays[-1].time_ended
        step_size = last_listen_time - first_listen_time
    
    return render_template('music.html', songs=tracks)
