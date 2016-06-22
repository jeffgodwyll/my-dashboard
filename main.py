import logging

from google.appengine.ext import ndb

from flask import Flask
from flask import render_template_string

import config
from utils import millis_to_time


app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']
app.jinja_env.filters['millis'] = millis_to_time

logger = logging.getLogger(__name__)

from activities import goodreads, googlefit, hn, lastfm, stackoverflow, twitter


TEMPLATE = """
{% for detail in details %}

<ul>
<b>Detail No.{{ loop.index }} for {{ detail.date }}</b>
<li>Number of twitter followers: {{ detail.twitter_followers }}</li>
<li>Number of tweets: {{ detail.tweets }}</li>
<li>Hacker News Karma: {{ detail.hn_karma }}</li>
<li>Number of Hacker News Links Submitted: {{ detail.hn_links }}</li>
<li>Number of Hours Slept: {{ detail.sleep | millis }}</li>
<li>Number of Steps: {{ detail.steps }}</li>
<li>Number of tracks scrobbled: {{ detail.tracks_scrobbled }}</li>
<li>Stackoverflow info: <code>{{ detail.stackoverflow}}</code></li>
<li>Goodreads info: <code>{{ detail.goodreads }}</code></li>
</ul>

</br>

{% endfor %}

"""


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
    return render_template_string(TEMPLATE, details=details)


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
