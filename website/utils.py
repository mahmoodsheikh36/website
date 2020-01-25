import uuid
import time

current_time = lambda: int(round(time.time() * 1000))

def random_str():
    return str(uuid.uuid4())
