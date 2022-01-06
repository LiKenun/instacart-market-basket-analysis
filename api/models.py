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
        if np.any(np.diff(self.data[5:]) <= 0):
            raise ValueError('Field \'data\' must contain only unique values sorted in ascending order from index 5.')

    def __hash__(self):
        return hash(tuple(self.data))

    def __repr__(self):
        return f'Suggestion({self.data!r})'

    def __str__(self):
        return f'Suggestion(' \
               f'consequent_item={self.consequent_item}, ' \
               f'transaction_count={self.transaction_count}, ' \
               f'item_set_count={self.item_set_count}, ' \
               f'antecedent_count={self.antecedent_count}, ' \
               f'consequent_count={self.consequent_count}, ' \
               f'antecedent_items={self.antecedent_items}, ' \
               f'lift={self.lift}, ' \
               f'support={self.support})'

    def __eq__(self, other):
        return np.array_equal(self.data, other.data)

    def __ge__(self, other):
        return (self.lift, self.support, self.data[0], tuple(self.data[5:])) <= \
               (other.lift, other.support, other.data[0], tuple(other.data[5:]))

    def __gt__(self, other):
        return (self.lift, self.support, self.data[0], tuple(self.data[5:])) < \
               (other.lift, other.support, other.data[0], tuple(other.data[5:]))

    def __le__(self, other):
        return (self.lift, self.support, self.data[0], tuple(self.data[5:])) >= \
               (other.lift, other.support, other.data[0], tuple(other.data[5:]))

    def __lt__(self, other):
        return (self.lift, self.support, self.data[0], tuple(self.data[5:])) > \
               (other.lift, other.support, other.data[0], tuple(other.data[5:]))

    def __ne__(self, other):
        return not np.array_equal(self.data, other.data)

    @property
    def consequent_item(self):
        return self.data[0]

    @property
    def transaction_count(self):
        return self.data[1]

    @property
    def item_set_count(self):
        return self.data[2]

    @property
    def antecedent_count(self):
        return self.data[3]

    @property
    def consequent_count(self):
        return self.data[4]

    @property
    def antecedent_items(self):
        return tuple(self.data[5:])

    @property
    def lift(self):
        return float(self.data[1]) * float(self.data[2]) / (float(self.data[3]) * float(self.data[4]))

    @property
    def support(self):
        return float(self.data[2]) / float(self.data[1])


__all__ = ('Suggestion',)
