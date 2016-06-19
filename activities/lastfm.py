import simplejson as json

from main import app, logger
from utils import http

http = http()


def scrobbled():
    """no of tracks scrobbled
    """
    fields = {
        'method': 'user.getRecentTracks',
        'user': app.config['LASTFM_USER'],
        'api_key': app.config['LASTFM_API_KEY'],
        'format': 'json'
    }

    url = 'http://ws.audioscrobbler.com/2.0'
    r = http.request('GET', url, fields=fields)
    resp = json.loads(r.data.decode('utf8'))
    # interested in the total for now, till "'from': 'date' is used in request
    scrobbled = resp['recenttracks']['@attr']['total']
    logger.info('lastfm tracks scrobbled: {}'.format(scrobbled))
    return scrobbled
