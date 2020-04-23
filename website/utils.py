import uuid
import time
import magic

current_time = lambda: int(round(time.time() * 1000))

def random_str():
    return str(uuid.uuid4())
