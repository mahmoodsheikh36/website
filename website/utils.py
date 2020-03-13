import uuid
import time
import magic

current_time = lambda: int(round(time.time() * 1000))

def random_str():
    return str(uuid.uuid4())

def get_mimetype(data: bytes):
    return magic.from_buffer(data, mime=True)

def get_mimetype_of_flask_file(flask_file):
    flask_file.seek(0)
    return get_mimetype(flask_file.read())
