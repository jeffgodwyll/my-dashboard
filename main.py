import simplejson as json
import logging

import twitter

from urllib3 import PoolManager
from urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox

from flask import Flask, jsonify, request, redirect, session, url_for

import config


app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']

logger = logging.getLogger(__name__)


@app.route('/oauth2callback')
def oauth2callback():
    if 'code' not in request.args:
        auth_uri = (
            'https://accounts.google.com/o/oauth2/v2/auth?response_type=code'
            '&client_id={}&redirect_uri={}&scope={}'.format(
                app.config['GOOGLE_CLIENT_ID'],
                app.config['GOOGLE_REDIRECT_URI'],
                app.config['SCOPE']))
        return redirect(auth_uri)
    else:
        auth_code = request.args.get('code')
        fields = {'code': auth_code,
                  'client_id': app.config['GOOGLE_CLIENT_ID'],
                  'client_secret': app.config['GOOGLE_CLIENT_SECRET'],
                  'redirect_uri': app.config['GOOGLE_REDIRECT_URI'],
                  'grant_type': 'authorization_code'
                  }
        if is_appengine_sandbox:
            http = AppEngineManager()
        else:
            http = PoolManager()

        r = http.request_encode_body(
            'POST', 'https://www.googleapis.com/oauth2/v4/token', fields=fields,
            encode_multipart=False)
        session['credentials'] = r.data  # r.text?
        return redirect(url_for('fit'))


@app.route('/stackoverflow')
def stackoverflow():
    if is_appengine_sandbox:
        http = AppEngineManager()
    else:
        http = PoolManager()
    req_uri = ('https://api.stackexchange.com/2.2/users/{}?order=desc&'
               'sort=reputation&site=stackoverflow&filter={}'.format(
                   app.config['STACKOVERFLOW_USER_ID'],
                   '!0Z-LvhH.LNOKu1BHWnIjY_iHH'))
    r = http.request('GET', req_uri)
    return jsonify(json.loads(r.data))


@app.route('/fit')
def fit():
    if 'credentials' not in session:
        return redirect(url_for('oauth2callback'))
    credentials = json.loads(session['credentials'])
    if credentials['expires_in'] <= 0:
        return redirect(url_for('oauth2callback'))
    else:
        headers = {
            'Authorization': 'Bearer {}'.format(credentials['access_token'])}
        req_uri = 'https://www.googleapis.com/fitness/v1/users/me/dataSources'

        if is_appengine_sandbox:
            http = AppEngineManager()
        else:
            http = PoolManager()

        r = http.request('GET', req_uri, headers=headers)
        resp = json.loads(r.data.decode('utf-8'))
        return jsonify(**resp)


@app.route('/lastfm')
def lastfm_tracks_scrobbled():
    fields = {
        'method': 'user.getRecentTracks',
        'user': app.config['LASTFM_USER'],
        'api_key': app.config['LASTFM_API_KEY'],
        'format': 'json'
    }

    if is_appengine_sandbox():
        http = AppEngineManager()
    else:
        http = PoolManager()

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
