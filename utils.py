from copy import copy
import datetime

from urllib3 import PoolManager
from urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox


def dictify(r, root=True):
    ''' Parses xml entities as dict regardless of attributes

    Courtesy: http://stackoverflow.com/a/30923963/2295256
    '''
    # TODO: Clean up to avoid 1 list items in result
    if root:
        return {r.tag: dictify(r, False)}
    d = copy(r.attrib)
    if r.text:
        d["_text"] = r.text
    for x in r.findall("./*"):
        if x.tag not in d:
            d[x.tag] = []
        d[x.tag].append(dictify(x, False))
    return d


def http():
    if is_appengine_sandbox:
        http = AppEngineManager()
    else:
        http = PoolManager()
    return http


def millis_to_time(millis):
    """Convert milliseconds to hours:minutes:seconds string
    """
    return str(datetime.timedelta(milliseconds=millis))


def today():
    """Returns a datetime object for today at midnight"""
    return datetime.datetime.combine(
        datetime.datetime.today().date(), datetime.datetime.min.time())


def yesterday():
    """Return yesterday as a datetime object"""
    return (today() - datetime.timedelta(days=1))


def datetime_to_millis(dt):
    """Returns datetime in milliseconds format."""
    epoch = datetime.datetime.utcfromtimestamp(0)
    return (dt-epoch).total_seconds() * 1000.0


def now():
    """The time now in milliseconds"""
    return int(datetime_to_millis(datetime.datetime.now()))


def yesterday_millis():
    """The time at midnight yesterday in milliseconds"""
    return int(datetime_to_millis(yesterday()))
