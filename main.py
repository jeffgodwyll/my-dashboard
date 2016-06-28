import logging

from google.appengine.ext import ndb

from flask import Flask
from flask import render_template

import config
from utils import millis_to_time, dateformat


app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']
app.jinja_env.filters['millis'] = millis_to_time
app.jinja_env.filters['dateformat'] = dateformat

logger = logging.getLogger(__name__)

from activities import goodreads, googlefit, hn, lastfm, stackoverflow, twitter

# TODO: Check for Nonetype  for timedelta milliseconds component in | millis
# filter, triggered when I hand inserted the values


################################################################################
# Models
class Details(ndb.Model):
    """Details. """
    twitter_followers = ndb.IntegerProperty(required=False)
    tweets = ndb.IntegerProperty(required=False)
    hn_karma = ndb.IntegerProperty(required=False)
    hn_links = ndb.IntegerProperty(required=False)
    sleep = ndb.IntegerProperty(required=False)
    steps = ndb.IntegerProperty(required=False)
    stackoverflow = ndb.JsonProperty(compressed=True, required=False)
    tracks_scrobbled = ndb.IntegerProperty(required=False)
    goodreads = ndb.JsonProperty(compressed=True, required=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


################################################################################
# Routes
@app.route('/')
def home():
    details = Details.query().order(-Details.date).fetch(10)
    return render_template('dash.html', details=details)


@app.route('/cron')
def detall():
    twitter_followers, tweets = twitter.stats()
    hn_karma, hn_links = hn.stats()
    details = Details()
    details.twitter_followers = twitter_followers
    details.tweets = tweets
    details.hn_karma = hn_karma
    details.hn_links = hn_links
    details.goodreads = goodreads.stats()
    details.tracks_scrobbled = lastfm.scrobbled()
    details.stackoverflow = stackoverflow.stats()
    details.sleep = googlefit.sleep()
    details.steps = googlefit.steps()
    details.put()
    return 'done'


if __name__ == '__main__':
    app.run(debug=True)
