import csv
from functools import partial
from io import TextIOBase, TextIOWrapper
from itertools import groupby, starmap, zip_longest
import lzma
from operator import ne
from toolz import apply, drop, identity, peek
from typing import Any, Callable, IO, Iterable, Optional, Protocol, Sequence, Type, TypeVar

T = TypeVar('T')
U = TypeVar('U')


class SupportsLessThan(Protocol):
    def __lt__(self, __other: Any) -> bool: ...


def create_csv_to_dataclass_mapper(data_class: Type[T], transform: dict[str, Callable[[str], Any]] = {}) \
        -> Callable[[Iterable[Sequence[str]]], Iterable[T]]:
    init_args = tuple(data_class.__annotations__.keys())
    transform = tuple(transform.get(arg, identity)
                      for arg in init_args)

    def function(iterable: Iterable[Sequence[str]]) -> Iterable[T]:
        header_row, iterable = peek(iterable)
        if any(starmap(ne, zip_longest(init_args, header_row))):  # Validate the order, names, and number of arguments.
            print(f'{init_args!r} != {header_row!r}')
            raise NotImplementedError()  # Other possibilities not yet supported
        for row in drop(1, iterable):
            yield data_class(*starmap(apply, zip(transform, row)))

    return function


def create_grouper(key: Optional[Callable[[T], U]] = None) -> Callable[[T], Iterable[tuple[U, Iterable[T]]]]:
    return partial(groupby, key=key)


def create_sorter(key: Optional[Callable[[T], SupportsLessThan]] = None, reverse: bool = False) \
        -> Callable[[Iterable], list[T]]:
    return partial(sorted, key=key, reverse=reverse)


def first(sequence: Sequence[T]) -> T:
    return sequence[0]


def is_sorted(comparison_operator: Callable[[T, T], bool], sequence: Sequence) -> bool:
    return all(starmap(comparison_operator, zip(sequence, sequence[1:])))


def read_compressed_csv(file: IO[bytes] | str, delimiter: str = '\t') -> Iterable[list[str]]:
    with lzma.open(file, 'rt', format=lzma.FORMAT_XZ, encoding='utf-8') as stream:
        for row in read_csv(stream, delimiter):
            yield row


def read_compressed_txt(file: IO[bytes] | str) -> Iterable[str]:
    with lzma.open(file, 'rt', format=lzma.FORMAT_XZ, encoding='utf-8') as stream:
        for line in stream:
            yield line.rstrip()


def read_csv(file: IO[bytes] | str | TextIOBase, delimiter: str = '\t') -> Iterable[list[str]]:
    if isinstance(file, TextIOBase):
        for row in csv.reader(file, delimiter=delimiter):
            yield row
    else:
        create_stream = open if isinstance(file, str) else TextIOWrapper
        with create_stream(file, encoding='utf-8') as stream:
            for row in csv.reader(stream, delimiter=delimiter):
                yield row


def second(sequence: Sequence[T]) -> T:
    return sequence[1]


def zipapply(functions: Iterable[Callable], arguments: Iterable) -> Iterable:
    return map(apply, functions, arguments)
