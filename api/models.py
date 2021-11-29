from dataclasses import dataclass
from typing import Optional


@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class Product:
    id: int
    name: str

    def __eq__(self, other):
        return self.id == other.id

    def __ge__(self, other):
        return self.id >= other.id

    def __gt__(self, other):
        return self.id > other.id

    def __hash__(self):
        return hash(self.id)

    def __le__(self, other):
        return self.id <= other.id

    def __lt__(self, other):
        return self.id < other.id

    def __ne__(self, other):
        return self.id != other.id


# See https://stackabuse.com/association-rule-mining-via-apriori-algorithm-in-python/ for the formulæ for confidence,
# lift, and support.
@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class Rule:
    base: tuple[Product, ...]
    additional: tuple[Product, ...]
    joint_count: int
    base_count: int
    additional_count: int
    transaction_count: int

    @property
    def confidence(self) -> Optional[float]:
        return self.joint_count / self.base_count

    @property
    def lift(self) -> Optional[float]:
        return (self.joint_count * self.transaction_count) / (self.additional_count * self.base_count)

    @property
    def support(self) -> Optional[float]:
        return self.additional_count / self.transaction_count

    def __eq__(self, other):
        return self.base == other.base and self.additional == other.additional

    def __ge__(self, other):
        return self.base > other.base or \
               self.base == other.base and self.additional >= other.additional

    def __gt__(self, other):
        return self.base > other.base or \
               self.base == other.base and self.additional > other.additional

    def __hash__(self):
        return hash((self.base, self.additional))

    def __le__(self, other):
        return self.base < other.base or \
               self.base == other.base and self.additional <= other.additional

    def __lt__(self, other):
        return self.base < other.base or \
               self.base == other.base and self.additional < other.additional

    def __ne__(self, other):
        return self.base != other.base or self.additional != other.additional


@dataclass(init=True, repr=True, eq=False, order=False, unsafe_hash=False, frozen=True)
class Suggestion:
    product: Product
    base: tuple[Product, ...]
    confidence: float
    lift: float

    def __eq__(self, other):
        return self.lift == other.lift and self.confidence == other.confidence and self.product.id == other.product.id

    def __ge__(self, other):
        return self.lift < other.lift or \
               self.lift == other.lift and self.confidence <= other.confidence or \
               self.lift == other.lift and self.confidence == other.confidence and self.product.id <= other.product.id

    def __gt__(self, other):
        return self.lift < other.lift or \
               self.lift == other.lift and self.confidence <= other.confidence or \
               self.lift == other.lift and self.confidence == other.confidence and self.product.id < other.product.id

    def __hash__(self):
        return hash((self.lift, self.confidence, self.product.id))

    def __le__(self, other):
        return self.lift > other.lift or \
               self.lift == other.lift and self.confidence >= other.confidence or \
               self.lift == other.lift and self.confidence == other.confidence and self.product.id > other.product.id

    def __lt__(self, other):
        return self.lift > other.lift or \
               self.lift == other.lift and self.confidence >= other.confidence or \
               self.lift == other.lift and self.confidence == other.confidence and self.product.id >= other.product.id

    def __ne__(self, other):
        return self.lift != other.lift or self.confidence != other.confidence or self.product.id != other.product.id
