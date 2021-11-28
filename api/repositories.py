from ast import literal_eval
from toolz import compose, pipe
from helpers import create_mapper, create_transform, read_compressed_csv
from models import Product, Rule


class ProductRepository:
    def __init__(self, products_data_file: str):
        self.__products_data_file = products_data_file

    def get_all_products(self) -> tuple[Product, ...]:
        return pipe(self.__products_data_file,
                    read_compressed_csv,
                    create_transform({'id': int}),
                    create_mapper(lambda parameters: Product(**parameters)),
                    tuple)


class RulesRepository:
    __parse_set = compose(frozenset, literal_eval)

    def __init__(self, rules_data_file: str):
        self.__rules_data_file = rules_data_file

    def get_all_association_rules(self) -> tuple[Rule, ...]:
        return pipe(self.__rules_data_file,
                    read_compressed_csv,
                    create_transform({'base': ProductRepository.__parse_set,
                                      'additional': ProductRepository.__parse_set,
                                      'joint_count': int,
                                      'base_count': int,
                                      'additional_count': int,
                                      'transaction_count': int}),
                    create_mapper(lambda parameters: Rule(**parameters)),
                    tuple)
