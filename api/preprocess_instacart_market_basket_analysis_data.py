from argparse import ArgumentParser
from collections import Counter, defaultdict, namedtuple
from efficient_apriori import apriori, Rule
from functools import partial
from itertools import chain, starmap
import os.path as path
from os.path import abspath
from toolz import apply, compose_left, drop, first, peek, second, thread_last
from typing import Any, Callable, Iterable, Optional
from zipfile import ZipFile
from helpers import read_csv, read_txt, unescape, write_compressed_csv, write_compressed_txt


def _parse_args() -> tuple[str, str, float, str]:
    parser = ArgumentParser(description='Mines association rules from Instacart’s market basket analysis data. Download'
                                        ' it from: https://www.kaggle.com/c/instacart-market-basket-analysis/data')
    parser.add_argument('--input', metavar='PATH', action='store', type=str,
                        default='instacart-market-basket-analysis.zip',
                        help='the Instacart market basket analysis data set')
    parser.add_argument('--exclusions', metavar='PATH', action='store', type=str, required=False,
                        help='a list of product identifiers to exclude')
    parser.add_argument('--minsupport', metavar='PERCENTAGE', action='store', type=float, required=False,
                        help='the minimum support (as a percentage of transactions) for any rule under consideration')
    parser.add_argument('--output', metavar='PATH', action='store', type=str,
                        help='the output directory to store the association rules and product list')
    args = parser.parse_args()
    input_path = abspath(args.input)
    exclusions_path = (abspath(args.exclusions)
                       if args.exclusions
                       else None)
    minsupport = (args.minsupport
                  if args.minsupport
                  else None)
    output_path = abspath(args.output or '')
    return input_path, exclusions_path, minsupport, output_path


def _preprocess(archive: ZipFile, exclusions: frozenset[int]) -> tuple[tuple[str], tuple[tuple[int, ...], ...]]:
    def read_csv_in_zip(inner_archive_name: str) -> Iterable[list[str]]:
        with archive.open(inner_archive_name) as inner_archive_file, \
             ZipFile(inner_archive_file) as inner_archive, \
             inner_archive.open(inner_archive_name.removesuffix('.zip')) as file:
            for row in read_csv(file, ','):
                yield row

    def create_transform(transform: dict[str, Callable[[str], Any]]) -> Callable[[Iterable[list[str]]], Iterable[tuple]]:
        def function(iterable: Iterable[list[str]]) -> Iterable[tuple]:
            header_row, iterable = peek(iterable)
            indices_to_extract, functions_to_apply = zip(*map({column_name: (index, transform[column_name])
                                                               for index, column_name in enumerate(header_row)
                                                               if column_name in transform}.get,
                                                              transform))
            namedtuple_type = namedtuple('AnonymousNamedTuple', transform)
            for row in drop(1, iterable):
                yield namedtuple_type(*starmap(apply, zip(functions_to_apply, map(lambda _: row[_], indices_to_extract))))
        return function

    print(' Loading products…')
    products = thread_last('products.csv.zip',
                           read_csv_in_zip,
                           create_transform({'product_id': int, 'product_name': unescape}),
                           (filter, lambda product: product.product_id not in exclusions),
                           partial(sorted, key=second))
    print(f' Loaded {len(products):,} products; excluded {len(exclusions):,} products.')
    orders = filter(lambda item: item.product_id not in exclusions,
                    chain.from_iterable(map(compose_left(read_csv_in_zip,
                                                         create_transform({'product_id': int, 'order_id': int})),
                                            ('order_products__prior.csv.zip', 'order_products__train.csv.zip'))))
    print(' Creating product identifier mapper…')
    map_product_identifier = dict(map(compose_left(reversed, tuple), enumerate(map(first, products)))).get
    print(' Creating transactions list…')
    transactions = defaultdict(set)
    for order in orders:
        transactions[order.order_id].add(map_product_identifier(order.product_id))
    print(f' Generated a list of {len(transactions):,} transactions.')
    return tuple(map(second, products)), tuple(map(tuple, transactions.values()))


def _train(transactions: Iterable[tuple[int]], min_support: Optional[float] = None) -> tuple[Rule]:
    product_counts = Counter(chain.from_iterable(transactions))
    transaction_count = len(transactions)
    null_base_rules = (Rule((), (product,), count, transaction_count, count, transaction_count)
                       for product, count in product_counts.items())
    item_sets, rules = apriori(transactions,
                               min_support=(100 / transaction_count
                                            if min_support is None
                                            else min_support),
                               min_confidence=0.0,
                               max_length=max(map(len, transactions)),
                               verbosity=1)
    return tuple(chain(null_base_rules, filter(lambda rule: rule.lift > 1, rules)))


def _dump(directory: str, products: tuple[str], rules: tuple[Rule]) -> None:
    products_path = path.join(directory, 'products.txt.xz')
    rules_path = path.join(directory, 'association_rules.tsv.xz')
    print(f' Writing {len(products):,} products to {products_path}…')
    write_compressed_txt(products_path, products)
    print(f' Writing {len(rules):,} rules to {rules_path}…')
    write_compressed_csv(rules_path,
                         ('antecedent_items', 'consequent_items', 'measure'),
                         (map(repr, (sorted(rule.lhs), sorted(rule.rhs), (rule.lift, rule.support)))
                          for rule in sorted(rules, key=lambda rule: (rule.lhs, rule.rhs))))


def run() -> None:
    input_path, exclusions_path, minsupport, output_path = _parse_args()
    print(f'Loading exclusions from {exclusions_path}…')
    exclusions = frozenset(map(int, read_txt(exclusions_path))
                           if exclusions_path is not None
                           else ())
    print(f'Preprocessing data from file {input_path}…')
    with ZipFile(input_path) as archive:
        products, transactions = _preprocess(archive, exclusions)
    print('Training…')
    rules = _train(transactions, minsupport)
    del transactions
    print(f'Saving products and rules to {output_path}…')
    _dump(output_path, products, rules)
    print('Done.')


if __name__ == '__main__':
    run()
