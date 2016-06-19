import simplejson as json

from main import app
from utils import http

http = http()


def stats():
    r = http.request(
        'GET', 'https://hacker-news.firebaseio.com/v0/user/{}.json'.format(
            app.config['HN_USER']))
    resp = json.loads(r.data)
    print type(resp)
    karma = int(resp.get('karma', 0))
    links = len(resp.get('submitted', 0))
    print links
    return karma, links
