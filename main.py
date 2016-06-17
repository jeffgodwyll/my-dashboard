import time
import logging
import xml.etree.ElementTree as ET
from copy import copy

import simplejson as json
import twitter

from flask import Flask, jsonify
from urllib3 import PoolManager
from urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox
import httplib2
from oauth2client import GOOGLE_TOKEN_URI
from oauth2client.client import GoogleCredentials
from apiclient.discovery import build

import config


app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']

logger = logging.getLogger(__name__)


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

http = http()


@app.route('/stackoverflow')
def stackoverflow():
    req_uri = ('https://api.stackexchange.com/2.2/users/{}?order=desc&'
               'sort=reputation&site=stackoverflow&filter={}'.format(
                   app.config['STACKOVERFLOW_USER_ID'],
                   '!0Z-LvhH.LNOKu1BHWnIjY_iHH'))
    r = http.request('GET', req_uri)
    resp = json.loads(r.data)
    logger.info('stackoverflow info: {}'.format(resp['items'][0]))
    return jsonify(resp)


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
    now = int(time.time()*1000)
    start = now - 1000*60*60*24
    datasets = service.users().dataset().aggregate(
        userId='me',
        body={
            'aggregateBy': [{
                'dataSourceId':
                app.config['GOOGLE_FIT_SOURCE'],
            }],
            'startTimeMillis': start,
            'endTimeMillis': now,
            'bucketByTime': {
                'durationMillis': 86400000,
                'period': 'day'
            },
            # 1 day = 86400000, 1hr = 3600000
        }
    ).execute()
    return datasets


@app.route('/steps')
def fit2():
    dataset = fit_datasets()
    buckets = dataset['bucket']
    total_steps = 0
    for bucket in buckets:
        for dataset in bucket['dataset']:
            total_steps += int(dataset['point'][0]['value'][0]['intVal'])
    return jsonify(dict(steps=total_steps))


@app.route('/fit_sources')
def fit_sources():
    sources = fit_datasources()
    return jsonify(dict(sources))
################################################################################


@app.route('/goodreads')
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
    return jsonify(**stats)


@app.route('/hn')
def hacker_news():
    r = http.request(
        'GET', 'https://hacker-news.firebaseio.com/v0/user/{}.json'.format(
            app.config['HN_USER']))
    resp = json.loads(r.data)
    print type(resp)
    hn = {
        'karma': resp['karma'],
        'noLinksSubmitted': len(resp['submitted']),
    }
    return jsonify(**hn)


@app.route('/lastfm')
def lastfm_tracks_scrobbled():
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
    tracks_scrobbled = resp['recenttracks']['@attr']['total']
    logger.info('lastfm tracks scrobbled: {}'.format(tracks_scrobbled))
    return jsonify(tracks_scrobbled=tracks_scrobbled)


def twitter_client():
    token = app.config['TWITTER_TOKEN']
    token_secret = app.config['TWITTER_TOKEN_SECRET']
    consumer_key = app.config['TWITTER_CONSUMER_KEY']
    consumer_secret = app.config['TWITTER_CONSUMER_SECRET']
    client = twitter.Twitter(
        auth=twitter.OAuth(token, token_secret, consumer_key, consumer_secret)
    )
    return client


@app.route('/twitter')
def twitter_details():
    service = twitter_client()
    req = service.statuses.user_timeline()
    follower_count = req[0]['user']['followers_count']
    tweet_count = req[0]['user']['statuses_count']
    twitter = {
        'follower_count': follower_count,
        'tweet_count': tweet_count,
    }
    logger.info('you have {0} followers and {1} tweets'.format(
        follower_count, tweet_count)
    )
    return jsonify(**twitter)


# TODO: save follower count with time to track changes over a period
# likewise for tweet count, can save such values in the datastore


if __name__ == '__main__':
    app.run(debug=True)
