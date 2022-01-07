from flask import Flask, jsonify, request, Response
from werkzeug.exceptions import HTTPException
from werkzeug.urls import url_parse
from repositories import ProductRepository, SuggestionRepository
from services import ProductLookupService


def create_app() -> Flask:  # TODO: Move views to a separate file
    app = Flask(__name__,
                static_folder='../build',
                static_url_path='/')
    product_lookup_service = ProductLookupService(ProductRepository('products.tsv.xz'),
                                                  SuggestionRepository('suggestions.npz.xz'))

    # See the Stack Overflow answer for why this is needed: https://stackoverflow.com/a/44572672/1405571.
    @app.after_request
    def add_cors_headers(response: Response) -> Response:
        referrer = url_parse(request.referrer[:-1]) \
                   if request.referrer \
                   else None
        if referrer.host and referrer.host == request.host:
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
        return jsonify({'data': product_lookup_service.get_suggestions(**request.json)})

    return app


flask_app = create_app()
