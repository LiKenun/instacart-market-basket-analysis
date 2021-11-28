from typing import NamedTuple


class Product(NamedTuple):
    id: int
    name: str


# See https://stackabuse.com/association-rule-mining-via-apriori-algorithm-in-python/ for the formulæ for confidence,
# lift, and support.
class Rule(NamedTuple):
    base: frozenset
    additional: frozenset
    joint_count: int
    base_count: int
    additional_count: int
    transaction_count: int

    @property
    def confidence(self):
        try:
            return self.joint_count / self.base_count
        except ZeroDivisionError:
            return None

    @property
    def lift(self):
        try:
            return self.confidence / self.additional_count
        except ZeroDivisionError:
            return None

    @property
    def support(self):
        try:
            return self.additional_count / self.transaction_count
        except ZeroDivisionError:
            return None
