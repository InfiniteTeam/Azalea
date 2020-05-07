import time

def makeid_by_time():
    twos = str(time.time()).split('.')
    return '{0}{1:0d<7}'.format(*twos)