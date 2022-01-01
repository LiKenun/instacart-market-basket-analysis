from ast import literal_eval
from dataclasses import dataclass
from toolz import compose_left, pipe
from helpers import create_csv_to_dataclass_mapper, read_compressed_csv, read_compressed_txt
from models import Measure, Rule


@dataclass(eq=False, frozen=True, slots=True)
class ProductRepository:
    products_data_file: str

    def get_all_products(self) -> tuple[str, ...]:
        return pipe(self.products_data_file,
                    read_compressed_txt,
                    tuple)


@dataclass(eq=False, frozen=True, slots=True)
class RulesRepository:
    rules_data_file: str

    __eval_tuple = compose_left(literal_eval, tuple)
    __eval_measure = lambda text: Measure(*literal_eval(text))

    def get_all_rules(self) -> tuple[Rule, ...]:
        return pipe(self.rules_data_file,
                    read_compressed_csv,
                    create_csv_to_dataclass_mapper(Rule, {'antecedent_items': RulesRepository.__eval_tuple,
                                                          'consequent_items': RulesRepository.__eval_tuple,
                                                          'measure': RulesRepository.__eval_measure}),
                    sorted,
                    tuple)


__all__ = ('ProductRepository', 'RulesRepository')
