import simplejson as json
from main import app, logger

from utils import http

http = http()


def stats():
    req_uri = ('https://api.stackexchange.com/2.2/users/{}?order=desc&'
               'sort=reputation&site=stackoverflow&filter={}'.format(
                   app.config['STACKOVERFLOW_USER_ID'],
                   '!0Z-LvhH.LNOKu1BHWnIjY_iHH'))
    r = http.request('GET', req_uri)
    resp = json.loads(r.data)
    logger.info('stackoverflow info: {}'.format(resp['items'][0]))
    return json.dumps(resp)
