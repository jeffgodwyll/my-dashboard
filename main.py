import logging

from google.appengine.ext import ndb

from flask import Flask
from flask import render_template_string

import config


app = Flask(__name__)
app.config.from_object(config)
app.secret_key = app.config['SECRET_KEY']

logger = logging.getLogger(__name__)

from activities import goodreads, googlefit, hn, lastfm, stackoverflow, twitter


TEMPLATE = """
{% for detail in details %}

<li>{{ detail }}</li>

{% endfor %}

"""


################################################################################
# Models
class Details(ndb.Model):
    """Docstring for Details. """
    twitter = ndb.JsonProperty(required=False)
    hn = ndb.JsonProperty(required=False)
    sleep = ndb.JsonProperty(required=False)
    steps = ndb.JsonProperty(required=False)
    stackoverflow = ndb.JsonProperty(required=False)
    lastfm = ndb.JsonProperty(required=False)
    goodreads = ndb.JsonProperty(required=False)
    date = ndb.DateTimeProperty(auto_now_add=True)


################################################################################
# Routes
@app.route('/')
def home():
    details = Details.query().order(-Details.date).fetch(10)
    return render_template_string(TEMPLATE, details=details)


@app.route('/cron')
def detall():
    details = Details()
    details.twitter = twitter.stats()
    details.hn = hn.stats()
    details.goodreads = goodreads.stats()
    details.lastfm = lastfm.scrobbled()
    details.stackoverflow = stackoverflow.stats()
    details.sleep = googlefit.sleep()
    details.steps = googlefit.steps()
    details.put()
    return 'done'


if __name__ == '__main__':
    app.run(debug=True)
