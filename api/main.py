from flask import Flask, request, Response
from repositories import ProductRepository, RulesRepository
from services import ProductLookupService

app = Flask(__name__,
            static_folder='../build',
            static_url_path='/')
__product_repository = ProductRepository('products.csv.xz')
__rules_repository = RulesRepository(__product_repository, 'association_rules.csv.xz')
__product_lookup_service = ProductLookupService(__product_repository, __rules_repository)


# See the Stack Overflow answer for why this is needed: https://stackoverflow.com/a/44572672/1405571.
@app.after_request
def add_cors_headers(response: Response) -> Response:
    referrer = request.referrer[:-1] \
               if request.referrer \
               else None
    if referrer in ('http://localhost:3000', 'http://localhost:5000'):
        response.headers.add('Access-Control-Allow-Origin', referrer)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'Cache-Control')
        response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS, POST')
    return response


@app.route('/')
def index() -> Response:
    return app.send_static_file('index.html')


@app.route('/api/suggestion', methods=['POST'])
def suggestion() -> dict[str, list[dict]]:
    request_data = request.json
    return_data = __product_lookup_service.get_suggestions(frozenset(request_data['basket']), request_data['query'])
    return {'data': return_data}


if __name__ == '__main__':
    app.run()
