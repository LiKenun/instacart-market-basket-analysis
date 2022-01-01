from flask import Flask, jsonify, request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.urls import url_parse
from repositories import ProductRepository, RulesRepository
from services import LemmatizerService, ProductLookupService

app = Flask(__name__,
            static_folder='../build',
            static_url_path='/')
__product_lookup_service = ProductLookupService(ProductRepository('products.txt.xz'),
                                                RulesRepository('association_rules.tsv.xz'),
                                                LemmatizerService())


# See the Stack Overflow answer for why this is needed: https://stackoverflow.com/a/44572672/1405571.
@app.after_request
def add_cors_headers(response: Response) -> Response:
    referrer = url_parse(request.referrer[:-1]) \
               if request.referrer \
               else None
    if referrer.host == request.host:
        response.headers.add('Access-Control-Allow-Origin', request.host_url)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'Cache-Control')
        response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS, POST')
    return response


@app.errorhandler(HTTPException)
def errorhandler(exception: HTTPException):
    if app.debug:
        return Response({'error': str(exception)}, 500)
    return exception, 500

@app.route('/')
def index() -> Response:
    return app.send_static_file('index.html')


@app.route('/api/suggestion', methods=['POST'])
def suggestion() -> Response:
    return jsonify({'data': __product_lookup_service.get_suggestions(**request.json)})


if __name__ == '__main__':
    app.run()
