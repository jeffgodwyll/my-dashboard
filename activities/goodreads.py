import xml.etree.ElementTree as ET

import simplejson as json

from main import app
from utils import dictify, http

http = http()


def stats():
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
