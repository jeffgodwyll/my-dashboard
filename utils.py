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


def millis_to_human(millis):
    """Convert milliseconds to human readable format
    """
    return str(datetime.timedelta(milliseconds=millis))


def http():
    if is_appengine_sandbox:
        http = AppEngineManager()
    else:
        http = PoolManager()
    return http
