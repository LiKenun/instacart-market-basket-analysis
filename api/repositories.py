from ast import literal_eval
from dataclasses import dataclass
from toolz import compose_left as compose
from helpers import create_csv_to_dataclass_mapper, read_compressed_csv, read_compressed_txt
from models import Measure, Rule


@dataclass(eq=False, frozen=True, slots=True)
class ProductRepository:
    products_data_file: str

    def get_all_products(self) -> tuple[str, ...]:
        return tuple(read_compressed_txt(self.products_data_file))


@dataclass(eq=False, frozen=True, slots=True)
class RulesRepository:
    rules_data_file: str

    __eval_tuple = compose(literal_eval, tuple)
    __eval_measure = lambda text: Measure(*literal_eval(text))
    __map_to_dataclass = create_csv_to_dataclass_mapper(Rule, {'antecedent_items': __eval_tuple,
                                                               'consequent_items': __eval_tuple,
                                                               'measure': __eval_measure})

    def get_all_rules(self) -> tuple[Rule, ...]:
        return tuple(sorted(RulesRepository.__map_to_dataclass(read_compressed_csv(self.rules_data_file))))


__all__ = ('ProductRepository', 'RulesRepository')
