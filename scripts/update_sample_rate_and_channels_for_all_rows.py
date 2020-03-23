#!/bin/python
# should be run from the project's parent directory
import sys
sys.path.insert(1, '../website')

import website.db
import website.ffmpeg

def get_file_path(db_file):
    return 'instance/files/{}'.format(db_file['name'])

db_conn = website.db.open_db('instance/data.sqlite')

db_files = db_conn.execute('SELECT * FROM files').fetchall()
for db_file in db_files:
    if not db_file['mimetype'].startswith('audio'):
        print('file {} is not audio'.format(db_file['id']))
        continue
    audio_stream_metadata =\
            website.ffmpeg.get_audio_stream_metadata(get_file_path(db_file))
    sample_rate = audio_stream_metadata['streams'][0]['sample_rate']
    channels = audio_stream_metadata['streams'][0]['channels']
    db_conn.execute('UPDATE songs SET sample_rate = ?, channels = ?\
                      WHERE audio_file_id = ?',
                     (sample_rate, channels, db_file['id'],))
    print('updated file {}'.format(db_file['id']))

db_conn.commit()
db_conn.close()
