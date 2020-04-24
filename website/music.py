import functools
from flask import (
    Blueprint, render_template
)

from website import db
from website.utils import get_largest_elements, current_time

from commandify.db import DBProvider
cmdify_db_provider = DBProvider()

bp = Blueprint('music', __name__, url_prefix='/music')

@bp.route('/', methods=('GET',))
def music_index():
    albums, tracks, artists, plays = cmdify_db_provider.get_music()

    for track in tracks:
        ms_listened = track.ms_listened()
        track.ms_listened_cached = ms_listened
        track.secs_listened = (ms_listened // 1000) % 60
        track.mins_listened = (ms_listened // 60000) % 60
        track.hrs_listened = (ms_listened // 360000)

    for track in tracks:
        first_listen_time = plays[0].time_started
        total_time = current_time() - first_listen_time
        time_fractions = 100
        time_step = total_time / time_fractions

    listening_data = []
    from_time = first_listen_time
    to_time = from_time + time_step
    for i in range(time_fractions):
        total = 0
        for track in tracks:
            total += track.ms_listened(from_time, to_time)
        listening_data.append(total)
        from_time = to_time
        to_time = from_time + time_step

    def compare(track1, track2):
        if track1.ms_listened_cached > track2.ms_listened_cached:
            return True
        return False
    
    return render_template('music.html',
                           songs=get_largest_elements(tracks, 100, compare),
                           listening_data=listening_data)
