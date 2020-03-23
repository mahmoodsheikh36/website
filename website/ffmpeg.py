import subprocess
import json

from website import db

def get_audio_stream_metadata(filepath):
    return json.loads(subprocess.check_output(
            ['ffprobe',
             '-loglevel',
             'panic',
             '-show_format',
             '-show_streams',
             '-select_streams',
             'a',
             '-of',
             'json',
             filepath]))
