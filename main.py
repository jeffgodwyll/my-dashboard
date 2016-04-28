import json

import twitter

from urllib import urlencode

from urllib3 import PoolManager
# from urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox

from flask import Flask, jsonify

import config


app = Flask(__name__)
app.config.from_object(config)


@app.route('/lastfm')
def lastfm_tracks_scrobbled():
    body = {
        'method': 'user.getrecenttracks',
        'user': app.config['LASTFM_USER'],
        'api_key': app.config['LASTFM_API_KEY'],
        # TODO: 'from': today?,
        'format': 'json'
    }

    # if is_appengine_sandbox():
    # http = AppEngineManager()
    # else:
    http = PoolManager()
    url = 'http://ws.audioscrobbler.com/2.0'
    r = http.request('GET', url, body=urlencode(body))
    resp = json.loads(r.data.decode('utf8'))
    # interested in the total for now, till "'from': 'date' is used in request
    tracks_scrobbled = resp['recenttracks']['@attr']['total']
    print 'tracks_scrobbled: {}'.format(tracks_scrobbled)
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
    return jsonify(**twitter)


# TODO: save follower count with time to track changes over a period
# likewise for tweet count, can save such values in the datastore


if __name__ == '__main__':
    app.run(debug=True)
