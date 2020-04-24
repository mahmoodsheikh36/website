import uuid
import time

current_time = lambda: int(round(time.time() * 1000))

def random_str():
    return str(uuid.uuid4())

def get_largest_elements(list_to_sort, limit, compare):
    mylist = list_to_sort.copy()
    final_list = []
    for i in range(limit):
        biggest = mylist[0]
        for j in range(len(mylist)):
            element = mylist[j]
            if compare(element, biggest):
                biggest = element
        final_list.append(biggest)
        mylist.remove(biggest)
    return final_list

def ms_to_time_str(ms):
    secs = (ms // 1000) % 60
    mins = (ms // 60000) % 60
    hrs = (ms // 3600000)
    str = ''
    if hrs == 1:
        str += '1 hr, '
    elif hrs > 1:
        str += '{} hrs, '.format(hrs)
    if mins == 1:
        str += '{} min, '
    elif mins > 1:
        str += '{} mins, '.format(mins)
    if secs == 1:
        str += '1 sec'
    elif secs > 1:
        str += '{} secs'.format(secs)
    return str
