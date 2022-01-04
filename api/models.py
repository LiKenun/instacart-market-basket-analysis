from dataclass_type_validator import dataclass_validate
from dataclasses import dataclass, field
from math import isnan
from operator import lt
from helpers import is_sorted


def _check_is_all_product_and_sorted(items: tuple, field_name: str):
    if not all(isinstance(item, Product) for item in items):
        raise TypeError(f'Field \'{field_name}\' must be a tuple of Product objects.')
    if not is_sorted(lt, items):
        raise ValueError(f'Field \'{field_name}\' must be sorted in ascending order and contain no duplicates.')


@dataclass_validate(strict=True, before_post_init=True)
@dataclass(order=True, frozen=True, slots=True)
class Measure:
    lift: float = 0.0
    support: float = 0.0

    def __post_init__(self):
        if self.lift < 0.0 or isnan(self.lift):
            raise ValueError('Field \'lift\' must be a non-negative number.')
        if self.support < 0.0 or 1.0 < self.support or isnan(self.support):
            raise ValueError('Field \'support\' must be between 0 and 1 (inclusive).')


@dataclass_validate(strict=True, before_post_init=True)
@dataclass(order=True, frozen=True, slots=True)
class Product:
    identifier: int
    name: str = field(hash=False, compare=False)

    def __post_init__(self):
        if self.identifier < 0:
            raise ValueError('Field \'identifier\' must be a non-negative integer.')
        if len(self.name) == 0:
            raise ValueError('Field \'name\' must be a non-empty string.')


@dataclass_validate(strict=True, before_post_init=True)
@dataclass(order=True, frozen=True, slots=True)
class Rule:
    antecedent_items: tuple
    consequent_items: tuple
    measure: Measure = field(hash=False, compare=False)

    def __post_init__(self):
        _check_is_all_product_and_sorted(self.antecedent_items, 'antecedent_items')
        if len(self.consequent_items) == 0:
            raise ValueError('Field \'consequent_items\' must contain at least one item.')
        _check_is_all_product_and_sorted(self.consequent_items, 'consequent_items')
        if not set(self.antecedent_items).isdisjoint(self.consequent_items):
            raise ValueError('An item may not be in both \'antecedent_items\' and \'consequent_items\'.')
        if self.measure.support <= 0.0:
            raise ValueError('Field \'support\' must be a positive value less than 1 (inclusive).')


@dataclass_validate(strict=True, before_post_init=True)
@dataclass(eq=False, unsafe_hash=True, frozen=True, slots=True)
class Suggestion:
    product: Product
    measure: Measure
    antecedent_items: tuple = ()
    rank: int = 0

    def __post_init__(self):
        _check_is_all_product_and_sorted(self.antecedent_items, 'antecedent_items')

    # The custom comparison implementations are needed to prioritize sorting in descending order.

    def __eq__(self, other):
        return self.rank == other.rank and \
               self.measure == other.measure and \
               self.product == other.product and \
               self.antecedent_items == other.antecedent_items

    def __ge__(self, other):
        return (self.rank, self.measure, self.product, self.antecedent_items) <= \
               (other.rank, other.measure, other.product, other.antecedent_items)

    def __gt__(self, other):
        return (self.rank, self.measure, self.product, self.antecedent_items) < \
               (other.rank, other.measure, other.product, other.antecedent_items)

    def __le__(self, other):
        return (self.rank, self.measure, self.product, self.antecedent_items) >= \
               (other.rank, other.measure, other.product, other.antecedent_items)

    def __lt__(self, other):
        return (self.rank, self.measure, self.product, self.antecedent_items) > \
               (other.rank, other.measure, other.product, other.antecedent_items)

    def __ne__(self, other):
        return self.rank != other.rank or \
               self.measure != other.measure or \
               self.product != other.product or \
               self.antecedent_items != other.antecedent_items


__all__ = ('Measure', 'Product', 'Rule', 'Suggestion')
