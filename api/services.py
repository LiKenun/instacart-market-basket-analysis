from collections import defaultdict
from fast_autocomplete import AutoComplete
from functools import reduce
from itertools import chain
import re
from typing import AbstractSet
from repositories import ProductRepository, RulesRepository


class ProductLookupService:
    __word_re = re.compile(r'[\w\d]+')

    def __init__(self, product_repository: ProductRepository, rules_repository: RulesRepository):
        self.__product_repository = product_repository
        self.__rules_repository = rules_repository
        self.__all_products = all_products = set()
        self.__id_table = id_table = {}
        self.__name_table = name_table = {}
        self.__product_id_index = product_id_index = dict()
        self.__product_name_index = product_name_index = defaultdict(set)
        for product in product_repository.get_all_products():
            all_products.add(product)
            id_table[product.id] = product.name
            name_table[product.name] = product.id
            product_id_index[product.id] = product
            for word in ProductLookupService.__word_re.findall(product.name.casefold()):
                product_name_index[word].add(product)
        autocomplete_words = {word: {}
                              for word
                              in product_name_index}
        self.autocomplete = AutoComplete(autocomplete_words)

    # TODO: incorporate association rules into the algorithm.
    def get_suggestions(self, basket: AbstractSet[int], query: str) -> list[dict]:
        term_groups = (set(chain.from_iterable(self.autocomplete.search(term)))
                       for term in ProductLookupService.__word_re.findall(query.casefold()))
        results = reduce(set.intersection,
                         (reduce(set.union,
                                 map(self.__product_name_index.get, term_group))
                          for term_group in term_groups),
                         self.__all_products)
        products_in_basket = map(self.__product_id_index.get, basket)
        return [product._asdict()
                for product
                in results.difference(products_in_basket)][:10]
