import time
from flask import Flask, request
from random import randint
from models import *
from services import *

__app = Flask(__name__,
              static_folder='../build',
              static_url_path='/')

__product_lookup_service = ProductLookupService()

# THis depends on pickle files (of models).
__prediction_service = None  # TODO: Singleton service class to provide predictive functions


# See this answer for why it’s needed: https://stackoverflow.com/a/44572672/1405571.
@__app.after_request
def add_cors_headers(response):
    referrer = request.referrer[:-1]
    if referrer in ('http://localhost:3000', 'http://localhost:5000'):
        response.headers.add('Access-Control-Allow-Origin', referrer)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'Cache-Control')
        response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS, POST')
    return response


@__app.route('/')
def index():
    return __app.send_static_file('index.html')


# Returns a list of suggestions given some input (e.g., the first 3 letters of a
# product and/or existing items in the shopping list)
@__app.route('/api/suggestion', methods=['POST'])
def suggestion():
    request_data = request.json
    return {'data': __product_lookup_service.get_by_query(request_data['query'])}
    # Cases:
    # 1. No items on list; use types in search bar
    #    * Index structure to reverse look up product id from text.
    #    * Results sorted by frequency of purchase. (No model needed)
    # 2. User has some items in the list; suggest additional items based on list.
    #    * Query association model for additional items.
    # 3. User has some items in the list and types in search bar; suggest based on both.
    #    * Query association model for additional items.
    #    * Intersect the item suggestions list with the results of a look up using the text.


@__app.route('/api/time')  # TODO: Remove; it was to check that the API server was working!
def get_current_time():
    return {'time': time.time()}


if __name__ == '__main__':
    __app.run()
