from dataclasses import dataclass
import numpy as np


@dataclass(init=True, repr=False, eq=False, frozen=True, slots=True)
class Suggestion:
    data: np.ndarray

    def __post_init__(self):
        if not (isinstance(self.data, np.ndarray) and self.data.dtype == np.uint32):
            raise TypeError('Field \'data\' must be a NumPy array of uint32.')
        if not (len(self.data.shape) == 1 and self.data.shape[0] >= 5):
            raise ValueError('Field \'data\' must be a one-dimensional array of at least 5 elements.')
        if not self.transaction_count > 0:
            raise ValueError('Field \'data\' at index 1 must be a non-zero value.')
        if not self.antecedent_count > 0:
            raise ValueError('Field \'data\' at index 3 must be a non-zero value.')
        if not self.consequent_count > 0:
            raise ValueError('Field \'data\' at index 4 must be a non-zero value.')
        if np.any(np.diff(self.data[5:]) <= 0):
            raise ValueError('Field \'data\' must contain only unique values sorted in ascending order from index 5.')

    def __hash__(self) -> int:
        return hash(tuple(self.data))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.data!r})'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(' \
               f'consequent_item={self.consequent_item}, ' \
               f'transaction_count={self.transaction_count}, ' \
               f'item_set_count={self.item_set_count}, ' \
               f'antecedent_count={self.antecedent_count}, ' \
               f'consequent_count={self.consequent_count}, ' \
               f'antecedent_items={self.antecedent_items}, ' \
               f'support={self.support}, ' \
               f'confidence={self.confidence}, ' \
               f'lift={self.lift})'

    def __eq__(self, other) -> bool:
        return np.array_equal(self.data, other.data)

    def __ge__(self, other) -> bool:
        return (self.lift, self.support, self.consequent_item, self.antecedent_items) <= \
               (other.lift, other.support, other.consequent_item, other.antecedent_items)

    def __gt__(self, other) -> bool:
        return (self.lift, self.support, self.consequent_item, self.antecedent_items) < \
               (other.lift, other.support, other.consequent_item, other.antecedent_items)

    def __le__(self, other) -> bool:
        return (self.lift, self.support, self.consequent_item, self.antecedent_items) >= \
               (other.lift, other.support, other.consequent_item, other.antecedent_items)

    def __lt__(self, other) -> bool:
        return (self.lift, self.support, self.consequent_item, self.antecedent_items) > \
               (other.lift, other.support, other.consequent_item, other.antecedent_items)

    def __ne__(self, other):
        return not np.array_equal(self.data, other.data)

    @property
    def consequent_item(self) -> np.int32:
        return self.data[0]

    @property
    def transaction_count(self) -> np.int32:
        return self.data[1]

    @property
    def item_set_count(self) -> np.int32:
        return self.data[2]

    @property
    def antecedent_count(self) -> np.int32:
        return self.data[3]

    @property
    def consequent_count(self) -> np.int32:
        return self.data[4]

    @property
    def antecedent_items(self) -> tuple[np.int32]:
        return tuple(self.data[5:])

    @property
    def support(self) -> float:
        return float(self.item_set_count) / float(self.transaction_count)

    @property
    def confidence(self) -> float:
        return float(self.item_set_count) / float(self.antecedent_count) \
               if self.antecedent_count != 0 \
               else float('inf')

    @property
    def lift(self) -> float:
        return float(self.transaction_count) * float(self.item_set_count) \
             / (float(self.antecedent_count) * float(self.consequent_count)) \
               if self.antecedent_count != 0 \
               else float('inf')


__all__ = ('Suggestion',)
