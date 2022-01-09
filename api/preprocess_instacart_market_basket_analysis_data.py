from ast import literal_eval
from argparse import ArgumentParser
from collections import Counter, defaultdict, namedtuple
import csv
from dataclasses import astuple, fields, is_dataclass
from efficient_apriori import apriori, Rule
from functools import partial
import html
from io import TextIOBase, TextIOWrapper
from itertools import chain, filterfalse, starmap
from nltk import download
from nltk.corpus import stopwords, wordnet as wn
from nltk.data import find
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tag import pos_tag
import numpy as np
import os.path as path
from os.path import abspath
from toolz import apply, compose_left as compose, identity, juxt, mapcat, thread_last as thread, unique
from typing import Any, Callable, IO, Iterable, Optional
from zipfile import ZipFile
from models import Suggestion
from helpers import first, read_csv, second, tokenize


def _ensure_nltk_data(names: Iterable[str]) -> None:
    for name in names:
        try:
            find(name)
        except LookupError:
            download(path.basename(name))


_ensure_nltk_data(('corpora/omw-1.4', 'corpora/stopwords', 'corpora/wordnet', 'taggers/averaged_perceptron_tagger',
                   'tokenizers/punkt'))
_lemmatizer = WordNetLemmatizer()


def _map_to_wordnet_pos(words: Iterable[tuple[str, str]]) -> Iterable[tuple[str] | tuple[str, str]]:
    for word, pos in words:
        match pos:
            case 'JJ' | 'JJR' | 'JJS' | 'PDT' | 'RP':
                yield word, wn.ADJ
            case 'CD' | 'NN' | 'NNS' | 'NNP' | 'NNPS':
                yield word, wn.NOUN
            case 'VB' | 'VBD' | 'VBG' | 'VBN' | 'VBP' | 'VBZ':
                yield word, wn.VERB
            case 'EX' | 'IN' | 'RB' | 'RBR' | 'RBS':
                yield word, wn.ADV
            case _:  # Other tags have no equivalent in WordNet.
                yield word, None


def _lemmatize_tagged_words(tagged_words: Iterable[tuple[str, Optional[str]]]) \
        -> Iterable[tuple[str, Optional[str]]]:
    for word, pos in tagged_words:
        if pos is not None and word != (lemma := _lemmatizer.lemmatize(word, pos)):
            yield lemma, word  # The lemmatized form takes precedence over the original.
        else:
            yield word, None


_lemmatize: Callable[[str], Iterable[tuple[str, Optional[str]]]] = \
    compose(str.lower,
            tokenize,
            partial(filterfalse, frozenset(stopwords.words('english')).__contains__),  # Filter out stop words.
            tuple,  # The next function does not work with Iterables, so it needs to be converted into a tuple.
            pos_tag,  # Tag each token (or “word”) with a part of speech (POS).
            _map_to_wordnet_pos,  # Map NLTK’s POS tags to WordNet’s tags.
            _lemmatize_tagged_words,
            partial(sorted, key=lambda lemma_word_pair: lemma_word_pair
                                                        if second(lemma_word_pair)
                                                        else (first(lemma_word_pair),)),
            unique)


def _parse_args() -> tuple[str, Optional[str], Optional[float], Optional[float], str]:
    parser = ArgumentParser(description='Mines association rules from Instacart’s market basket analysis data. Download'
                                        ' it from: https://www.kaggle.com/c/instacart-market-basket-analysis/data')
    parser.add_argument('--input', metavar='PATH', action='store', type=str,
                        default='instacart-market-basket-analysis.zip',
                        help='the Instacart market basket analysis data set')
    parser.add_argument('--exclusions', metavar='PATH', action='store', type=str, required=False,
                        help='a list of product identifiers to exclude')
    parser.add_argument('--minsupport', metavar='PERCENTAGE', action='store', type=float, required=False,
                        help='the minimum support (as a percentage of transactions) for any rule under consideration')
    parser.add_argument('--minconf', metavar='PERCENTAGE', action='store', type=float, required=False,
                        help='the minimum confidence for any rule under consideration')
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
    minconf = (args.minconf
               if args.minconf
               else None)
    output_path = abspath(args.output or '')
    return input_path, exclusions_path, minsupport, minconf, output_path


def _preprocess(archive: ZipFile, exclusions: frozenset[int]) -> tuple[tuple[str], tuple[tuple[int, ...], ...]]:
    def read_csv_in_zip(inner_archive_name: str) -> Iterable[list[str]]:
        with archive.open(inner_archive_name) as inner_archive_file, \
             ZipFile(inner_archive_file) as inner_archive, \
             inner_archive.open(inner_archive_name.removesuffix('.zip')) as file:
            for row in read_csv(file, ','):
                yield row

    def create_transform(transform: dict[str, Callable[[str], Any]]) -> Callable[[Iterable[list[str]]], Iterable[tuple]]:
        def function(iterable: Iterable[list[str]]) -> Iterable[tuple]:
            header_row = next(iterable := iter(iterable))
            indices_to_extract, functions_to_apply = zip(*map({column_name: (index, transform[column_name])
                                                               for index, column_name in enumerate(header_row)
                                                               if column_name in transform}.get,
                                                              transform))
            namedtuple_type = namedtuple('AnonymousNamedTuple', transform)
            for row in iterable:
                yield namedtuple_type(*starmap(apply, zip(functions_to_apply, map(lambda _: row[_], indices_to_extract))))
        return function

    print(' Loading products…')
    products: list[tuple[int, str]] = \
        thread('products.csv.zip',
               read_csv_in_zip,
               create_transform({'product_id': int, 'product_name': _unescape}),
               (filter, lambda product: product.product_id not in exclusions),
               partial(sorted, key=second))
    print(f'  Loaded {len(products):,} products; excluded {len(exclusions):,} products.')
    orders = filter(lambda item: item.product_id not in exclusions,
                    chain.from_iterable(map(compose(read_csv_in_zip,
                                                    create_transform({'product_id': int, 'order_id': int})),
                                            ('order_products__prior.csv.zip', 'order_products__train.csv.zip'))))
    map_product_identifier = dict(map(compose(reversed, tuple), enumerate(map(first, products)))).get
    print(' Creating transactions list…')
    transactions: defaultdict[str, set[int]] = defaultdict(set)
    for order in orders:
        transactions[order.order_id].add(map_product_identifier(order.product_id))
    print(f'  Generated a list of {len(transactions):,} transactions.')
    return (tuple(map(second, products)),
            tuple(tuple(transaction)
                  for transaction
                  in transactions.values()))


def _train(transactions: tuple[tuple[int, ...]], min_support: Optional[float] = None,
           min_confidence: Optional[float] = None) -> tuple[Rule, ...]:
    product_counts = Counter(chain.from_iterable(transactions))
    transaction_count = len(transactions)
    null_base_rules = (Rule((), (product,), count, transaction_count, count, transaction_count)
                       for product, count in product_counts.items())
    item_sets, rules = apriori(transactions,
                               min_support=(100 / transaction_count
                                            if min_support is None
                                            else min_support),
                               min_confidence=(1 / 10
                                               if min_confidence is None
                                               else min_confidence),
                               max_length=max(map(len, transactions)),
                               verbosity=1)
    return tuple(chain(null_base_rules, filter(lambda rule: rule.lift > 1, rules)))


def _convert_rules_to_suggestions(rules: tuple[Rule, ...]) -> list[np.array]:
    return thread(rules,
                  (mapcat, lambda rule: ((item, rule.num_transactions, rule.count_full, rule.count_lhs, rule.count_rhs,
                                          *sorted(rule.lhs))
                                         for item in rule.rhs)),
                  partial(map, compose(partial(np.array, dtype=np.uint32), Suggestion)),
                  sorted,
                  (map, lambda suggestion: suggestion.data),
                  list)


def _dump(directory: str, products: tuple[tuple[str, list[tuple[str, Optional[str]]]], ...], suggestions: list[np.array]) \
        -> None:
    products_path = path.join(directory, 'products.tsv')
    suggestions_path = path.join(directory, 'suggestions.npz')

    print(f' Writing {len(products):,} products to {products_path}…')
    _write_csv(products_path,
               None,
               thread(products,
                      (starmap, lambda product_name, lemma_word_pairs: (product_name, repr(lemma_word_pairs)))))

    print(f' Writing {len(suggestions):,} rules to {suggestions_path}…')
    # See https://tonysyu.github.io/ragged-arrays.html for the method to save/load ragged arrays with NumPy.
    lengths = [np.shape(array)[0] for array in suggestions]
    indices = np.cumsum(lengths[:-1])
    array = np.concatenate(suggestions)
    with open(suggestions_path, 'wb') as file:
        np.savez(file, array=array, indices=indices)


def _is_namedtuple_instance(value: Any) -> bool:
    return (isinstance(value, tuple) and
            hasattr(value, '_fields') and
            isinstance(value._fields, tuple) and
            all(type(item) == str for item in value._fields))


def _read_txt(file: IO[bytes] | str | TextIOBase) -> Iterable[str]:
    with open(file, encoding='utf-8') as stream:
        for line in stream:
            yield line.rstrip()


def _unescape(value: str) -> str:
    return html.unescape(literal_eval(f'"{value}"'))


def _write_csv_to_text_stream(file: TextIOBase, column_names: Optional[Iterable], data: Any, delimiter: str = '\t') \
        -> None:
    writer = csv.writer(file, dialect=csv.unix_dialect, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
    if column_names is None:
        first_row = next(iterator := iter(data))
        if isinstance(first_row, dict):
            column_names = first_row.keys()
            rows = (map(row.get, column_names) for row in iterator)
        elif is_dataclass(first_row):
            column_names = (field.name for field in fields(first_row))
            rows = map(astuple, iterator)
        elif _is_namedtuple_instance(first_row):
            column_names = first_row._fields
            rows = iterator
        elif isinstance(first_row, Iterable):
            column_names = first_row
            rows = iterator
        else:
            column_names = tuple(vars(first_row).keys())
            rows = (map(partial(getattr, row), column_names) for row in iterator)
    else:
        rows = data
    writer.writerow(column_names)
    writer.writerows(rows)


def _write_csv(file: IO[bytes] | str | TextIOBase, column_names: Optional[Iterable], data: Any, delimiter: str = '\t') \
        -> None:
    if isinstance(file, TextIOBase):
        _write_csv_to_text_stream(file, column_names, data, delimiter)
    else:
        if isinstance(file, str):
            with open(file, 'wt', encoding='utf-8', newline='') as stream:
                _write_csv(stream, column_names, data)
        else:
            with TextIOWrapper(file, encoding='utf-8', newline='') as stream:
                _write_csv(stream, column_names, data)


def run() -> None:
    input_path, exclusions_path, minsupport, minconf, output_path = _parse_args()
    print(f'Loading exclusions from {exclusions_path}…')
    exclusions = frozenset(map(int, _read_txt(exclusions_path))
                           if exclusions_path is not None
                           else ())
    print(f'Preprocessing data from file {input_path}…')
    with ZipFile(input_path) as archive:
        products, transactions = _preprocess(archive, exclusions)
    del exclusions
    print('Lemmatizing product names…')
    products_with_lemmas = thread(products,
                                  (map, juxt(identity, compose(_lemmatize, list))),
                                  tuple)
    del products
    print('Training…')
    rules = _train(transactions, minsupport, minconf)
    del transactions
    print('Generating suggestions…')
    suggestions = _convert_rules_to_suggestions(rules)
    del rules
    print(f'Saving products and rules to {output_path}…')
    _dump(output_path, products_with_lemmas, suggestions)


if __name__ == '__main__':
    run()
