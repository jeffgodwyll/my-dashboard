import twitter as tw
from main import app, logger


def client():
    token = app.config['TWITTER_TOKEN']
    token_secret = app.config['TWITTER_TOKEN_SECRET']
    consumer_key = app.config['TWITTER_CONSUMER_KEY']
    consumer_secret = app.config['TWITTER_CONSUMER_SECRET']
    client = tw.Twitter(
        auth=tw.OAuth(token, token_secret, consumer_key, consumer_secret)
    )
    return client


def stats():
    """
    :returns: number of followers and number of tweets
    """
    service = client()
    req = service.statuses.user_timeline()
    followers = req[0]['user']['followers_count']
    tweets = req[0]['user']['statuses_count']
    logger.info('you have {0} followers and {1} tweets'.format(
        followers, tweets))
    return followers, tweets
