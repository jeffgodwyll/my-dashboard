import time

from oauth2client import GOOGLE_TOKEN_URI
from oauth2client.client import GoogleCredentials
from apiclient.discovery import build
import httplib2

from main import app, logger
from utils import http

http = http()

NOW = int(time.time()*1000)
START = NOW - 1000*60*60*24


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
