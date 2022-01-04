from ast import literal_eval
from dataclasses import dataclass
from functools import cache, partial
from itertools import starmap
from toolz import compose_left as compose, thread_last as thread
from helpers import create_csv_to_dataclass_mapper, read_compressed_csv, read_compressed_txt
from models import Measure, Product, Rule


@dataclass(eq=False, frozen=True, slots=True)
class ProductRepository:
    products_data_file: str

    @cache
    def get_all_products(self) -> tuple[Product, ...]:
        return thread(self.products_data_file,
                      read_compressed_txt,
                      enumerate,  # Numbers each product starting from 0; it’s both the product identifier and index
                      (starmap, Product),
                      tuple)  # Index equals product identifier


@dataclass(eq=False, frozen=True, slots=True)
class RuleRepository:
    product_repository: ProductRepository  # Needed to replace product identifiers by their corresponding Product object
    rules_data_file: str

    @cache
    def get_all_rules(self) -> tuple[Rule, ...]:
        eval_tuple = compose(literal_eval,
                             partial(map, self.product_repository.get_all_products().__getitem__),
                             tuple)
        return thread(self.rules_data_file,
                      read_compressed_csv,
                      create_csv_to_dataclass_mapper(Rule,
                                                     {'antecedent_items': eval_tuple,
                                                      'consequent_items': eval_tuple,
                                                      'measure': lambda text: Measure(*literal_eval(text))}),
                      sorted,
                      tuple)


__all__ = ('ProductRepository', 'RuleRepository')
