from efficient_apriori import apriori, Rule
from collections import Counter, defaultdict
from itertools import chain
import sys
from toolz import pipe
from typing import Any, Callable, Iterable, Union
from zipfile import ZipFile
from helpers import create_mapper, create_transform, read_csv, unescape, write_compressed_csv
from models import Product


# This function expects a zip file downloaded from Kaggle.
# Visit: https://www.kaggle.com/c/instacart-market-basket-analysis/data
def __preprocess(path: str = 'instacart-market-basket-analysis.zip') -> tuple[tuple[Product], tuple[tuple[int, ...], ...]]:
    with ZipFile(path) as archive:
        def read_csv_in_zip(inner_archive_name: str) -> Iterable[list[str]]:
            with archive.open(inner_archive_name) as inner_archive_file:
                with ZipFile(inner_archive_file) as inner_archive:
                    with inner_archive.open(inner_archive_name.removesuffix('.zip')) as file:
                        for row in read_csv(file):
                            yield row
        products = __preprocess_products(read_csv_in_zip)
        orders = __preprocess_orders(read_csv_in_zip)
        transactions = __preprocess_transactions(orders)
        return products, transactions


def __preprocess_orders(reader: Callable[[str], Iterable[list[str]]]) -> Iterable[dict[str, Any]]:
    return pipe(('prior', 'train'),
                create_mapper('order_products__{}.csv.zip'.format),
                create_mapper(reader),
                create_mapper(create_transform({'product_id': int,
                                                'order_id': int})),
                chain.from_iterable)


def __preprocess_products(reader: Callable[[str], Iterable[list[str]]]) -> tuple[Product]:
    return pipe('products.csv.zip',
                reader,
                create_transform({'product_id': int,
                                  'product_name': unescape}),
                create_mapper(lambda _: Product(_['product_id'], _['product_name'])),
                tuple)


def __preprocess_transactions(orders: Iterable[dict[str, Any]]) -> tuple[tuple[int, ...], ...]:
    results = defaultdict(set)
    for order in orders:
        results[order['order_id']].add(order['product_id'])
    return tuple(map(tuple, results.values()))


def __train(transactions: Iterable[Union[set[int], tuple[int], list[int]]]) -> Iterable[Rule]:
    product_counts = Counter(chain.from_iterable(transactions))
    transaction_count = sum(product_counts.values())
    null_base_rules = (Rule((), (product,), count, transaction_count, count, transaction_count)
                       for product, count in product_counts.items())
    item_sets, rules = apriori(transactions,
                               min_support=200 / 3346083,
                               min_confidence=0.01,
                               max_length=3,
                               verbosity=1)
    return chain(null_base_rules, filter(lambda rule: rule.lift > 1, rules))


def __dump(products: Iterable[Product], rules: Iterable[Rule]) -> None:
    write_compressed_csv('products.csv.xz', None, products)
    write_compressed_csv('association_rules.csv.xz',
                         ('base', 'additional', 'joint_count', 'base_count', 'additional_count', 'transaction_count'),
                         (map(repr, (rule.lhs, rule.rhs, rule.count_full, rule.count_lhs, rule.count_rhs, rule.num_transactions))
                          for rule in rules))


def run() -> None:
    print('Preprocessing data…')
    products, transactions = __preprocess(*sys.argv[1:])
    print('Training…')
    rules = __train(transactions)
    print('Saving products and rules…')
    __dump(products, rules)
    print('Done.')


if __name__ == '__main__':
    run()
