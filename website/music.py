import functools
from flask import (
    Blueprint, render_template
)

from website import db
from website.utils import current_time

from pmus.db import MusicProvider

bp = Blueprint('music', __name__, url_prefix='/music')

@bp.route('/', methods=('GET',))
def music_index():
    songs = []
    return render_template('music.html')
