from ast import literal_eval
from sortedcontainers import SortedSet
from toolz import pipe
from typing import Callable
from helpers import create_dict_to_dataclass_mapper, create_transform, read_compressed_csv
from models import Product, Rule


class ProductRepository:
    def __init__(self, products_data_file: str):
        self.__products_cache = None
        self.__products_data_file = products_data_file

    def get_all_products(self) -> SortedSet[Product]:
        if self.__products_cache is None:
            self.__products_cache = pipe(self.__products_data_file,
                                         read_compressed_csv,
                                         create_transform({'id': int}),
                                         create_dict_to_dataclass_mapper(Product),
                                         frozenset)
        return SortedSet(self.__products_cache)


class RulesRepository:
    def __init__(self, product_repository: ProductRepository, rules_data_file: str):
        self.__product_repository = product_repository
        self.__rules_cache = None
        self.__rules_data_file = rules_data_file

    @staticmethod
    def __create_product_set_transform(products_dictionary: dict[int, Product]) -> Callable[[str], tuple[Product, ...]]:
        def function(value: str) -> tuple[Product, ...]:
            return tuple(products_dictionary[product_id]
                         for product_id in literal_eval(value))
        return function

    def get_all_rules(self) -> SortedSet[Rule]:
        if self.__rules_cache is None:
            products_dictionary = {product.id: product
                                   for product in self.__product_repository.get_all_products()}
            product_set_transform = RulesRepository.__create_product_set_transform(products_dictionary)
            self.__rules_cache = pipe(self.__rules_data_file,
                                      read_compressed_csv,
                                      create_transform({'base': product_set_transform,
                                                        'additional': product_set_transform,
                                                        'joint_count': int,
                                                        'base_count': int,
                                                        'additional_count': int,
                                                        'transaction_count': int}),
                                      create_dict_to_dataclass_mapper(Rule),
                                      frozenset)
        return SortedSet(self.__rules_cache)
