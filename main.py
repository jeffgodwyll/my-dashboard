import datetime
import time
import logging
import xml.etree.ElementTree as ET
from copy import copy

from google.appengine.ext import ndb

import simplejson as json
import twitter

from flask import Flask
from urllib3 import PoolManager
from urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox
import httplib2
from oauth2client import GOOGLE_TOKEN_URI
from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

import config

NOW = int(time.time()*1000)
START = NOW - 1000*60*60*24

app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']

logger = logging.getLogger(__name__)


################################################################################
# Utils

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

http = http()


################################################################################
# Models
class Details(ndb.Model):

    """Docstring for Details. """
    twitter = ndb.JsonProperty(required=False)
    hn = ndb.JsonProperty(required=False)
    slept = ndb.JsonProperty(required=False)
    steps = ndb.JsonProperty(required=False)
    stackoverflow = ndb.JsonProperty(required=False)
    lastfm = ndb.JsonProperty(required=False)
    goodreads = ndb.JsonProperty(required=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


################################################################################
# Stackoverflow
def stackoverflow():
    req_uri = ('https://api.stackexchange.com/2.2/users/{}?order=desc&'
               'sort=reputation&site=stackoverflow&filter={}'.format(
                   app.config['STACKOVERFLOW_USER_ID'],
                   '!0Z-LvhH.LNOKu1BHWnIjY_iHH'))
    r = http.request('GET', req_uri)
    resp = json.loads(r.data)
    logger.info('stackoverflow info: {}'.format(resp['items'][0]))
    return json.dumps(resp)


################################################################################
# Google Fit
def fit_client():
    """ build google fit service
    """
    credentials = GoogleCredentials(
        access_token=None,
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        refresh_token=app.config['GOOGLE_REFRESH_TOKEN'],
        token_expiry=None,
        token_uri=GOOGLE_TOKEN_URI,
        user_agent="My Dashboard",
    )
    http = httplib2.Http()
    http = credentials.authorize(http)

    return build('fitness', 'v1', http=http)


def fit_datasources():
    """fit datasources

    :returns: fit datasources

    """
    service = fit_client()
    datasources = service.users().dataSources().list(userId='me').execute()
    return datasources


def fit_sessions():
    """return fit sessions"""
    service = fit_client()
    sessions = service.users().sessions().list(userId='me').execute()
    return sessions


def fit_datasets():
    """Fit datasets

    :returns: google fit datasets

    """
    service = fit_client()

    datasets = service.users().dataset().aggregate(
        userId='me',
        body={
            'aggregateBy': [{
                'dataSourceId':
                app.config['GOOGLE_FIT_SOURCE'],
            }],
            'startTimeMillis': START,
            'endTimeMillis': NOW,
            'bucketByTime': {
                'durationMillis': 86400000,
                'period': 'day'
            },
            # 1 day = 86400000, 1hr = 3600000
        }
    ).execute()
    return datasets


def sleep():
    """ return number no of hours slept in a day
    """
    sessions = fit_sessions()
    duration = 0
    for session in sessions['session']:
        start_sleep = int(session['startTimeMillis'])
        end_sleep = int(session['endTimeMillis'])
        if session['activityType'] == 72 and start_sleep >= START:
            duration += (end_sleep - start_sleep)
    return duration


def steps():
    dataset = fit_datasets()
    buckets = dataset['bucket']
    steps = 0
    for bucket in buckets:
        for dataset in bucket['dataset']:
            steps += int(dataset['point'][0]['value'][0]['intVal'])
    print 'steps are: ', steps
    return steps


################################################################################
# Goodreads
def goodreads():
    req = http.request(
        'GET', 'https://www.goodreads.com/user/show/{}.xml?key={}'.format(
            app.config['GOODREADS_USERID'], app.config['GOODREADS_KEY']))
    r = dictify(ET.fromstring(req.data))
    user = r['GoodreadsResponse']['user'][0]
    friends_count = int(user['friends_count'][0]['_text'])
    reviews_count = int(user['reviews_count'][0]['_text'])
    fav_genres = user['favorite_books'][0]['_text'].split(', ')
    shelves = user['user_shelves'][0]['user_shelf']
    shelf_info = {
        shelf['name'][0]['_text']: int(shelf['book_count'][0]['_text'])
        for shelf in shelves}
    stats = {
        'friendsCount': friends_count,
        'reviewsCount': reviews_count,
        'books': {
            'numberShelves': len(shelves),
            'shelves': shelf_info,
        },
        'favoriteGenres': fav_genres,
    }
    return json.dumps(stats)


################################################################################
# Hacker News
def hacker_news():
    r = http.request(
        'GET', 'https://hacker-news.firebaseio.com/v0/user/{}.json'.format(
            app.config['HN_USER']))
    resp = json.loads(r.data)
    print type(resp)
    karma = resp['karma']
    links = resp['submitted']
    return karma, links


################################################################################
# Lastfm
def lastfm_tracks_scrobbled():
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


################################################################################
# Twitter
def twitter_client():
    token = app.config['TWITTER_TOKEN']
    token_secret = app.config['TWITTER_TOKEN_SECRET']
    consumer_key = app.config['TWITTER_CONSUMER_KEY']
    consumer_secret = app.config['TWITTER_CONSUMER_SECRET']
    client = twitter.Twitter(
        auth=twitter.OAuth(token, token_secret, consumer_key, consumer_secret)
    )
    return client


def twitter_stats():
    """
    :returns: number of followers and number of tweets
    """
    service = twitter_client()
    req = service.statuses.user_timeline()
    followers = req[0]['user']['followers_count']
    tweets = req[0]['user']['statuses_count']
    logger.info('you have {0} followers and {1} tweets'.format(
        followers, tweets))
    return (followers, tweets)


@app.route('/cron')
def getall():
    details = Details()
    details.twitter = twitter_stats()
    details.hn = hacker_news()
    details.goodreads = goodreads()
    details.lastfm = lastfm_tracks_scrobbled()
    details.stackoverflow = stackoverflow()
    details.sleep = sleep()
    details.steps = steps()
    details.put()
    return 'done'


if __name__ == '__main__':
    app.run(debug=True)
