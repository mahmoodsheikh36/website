import subprocess
import json

from website import db

def get_audio_stream_format_data(file_id):
    filepath = db.get_file_path(file_id)
    return json.loads(subprocess.check_output(
            ['ffprobe',
             '-loglevel',
             'panic',
             '-show_format',
             '-select_streams',
             'a:1',
             '-of',
             'json',
             filepath]))['format']
