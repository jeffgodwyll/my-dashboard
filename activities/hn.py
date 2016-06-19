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
    karma = resp.get('karma', 0)
    links = resp.get('submitted', 0)
    return karma, links
