import datetime
from dateutil.relativedelta import relativedelta

def get_timedelta(delta: datetime.timedelta):
    msecs = delta / datetime.timedelta(microseconds=1)
    return relativedelta(microseconds=msecs)

def format_timedelta(delta: datetime.timedelta):
    d = get_timedelta(delta)
    ds = {}
    if d.years:
        ds['years'] = '{}년'.format(int(d.years))
    if d.months:
        ds['months'] = '{}월'.format(int(d.months))
    if d.days:
        ds['days'] = '{}일'.format(int(d.days))
    if d.hours:
        ds['hours'] = '{}시간'.format(int(d.hours))
    if d.minutes:
        ds['minutes'] = '{}분'.format(int(d.minutes))
    if d.seconds:
        ds['seconds'] = '{}초'.format(int(d.seconds))
    return ds