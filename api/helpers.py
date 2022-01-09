import csv
from functools import partial
from io import TextIOBase, TextIOWrapper
import re
from toolz import apply, compose_left as compose
from typing import Any, Callable, IO, Iterable, Protocol, TypeVar

T = TypeVar('T')
U = TypeVar('U')


class SupportsLessThan(Protocol):
    def __lt__(self, __other) -> bool: ...


def first(sequence: tuple[T, U]) -> T:
    return sequence[0]


def read_csv(file: IO[bytes] | str | TextIOBase, delimiter: str = '\t') -> Iterable[list[str]]:
    if isinstance(file, TextIOBase):
        for row in csv.reader(file, delimiter=delimiter):
            yield row
    else:
        create_stream = open if isinstance(file, str) else TextIOWrapper
        with create_stream(file, encoding='utf-8') as stream:
            for row in csv.reader(stream, delimiter=delimiter):
                yield row


def second(sequence: tuple[T, U]) -> U:
    return sequence[1]


def star(function: Callable, arguments: Iterable) -> Any:
    return function(*arguments)


tokenize: Callable[[str], Iterable[str]] = \
    compose(re.compile('|'.join((r'(?:(?<=^)|(?<=[\s(]))(?:#|No.?\s*){numeric_re}\+?(?=,?\s|\)|$)',
                                 r'(?:(?<=^)|(?<=[\s(])){numeric_re}(?:(?:\'s|["\'+])|\s*(?:%|c(?:oun)?t\.?|cups?'
                                 r'|(?:fl\.?\s)?oz\.?|in(?:\.|ch(?:es)?)?|lbs?\.?|mgs?\.?|only|ounces?|p(?:ac)?k'
                                 r'|pcs?\.?|pieces?|pounds?|size|x))?(?=,?\s|\)|$)',
                                 r'[^\s!"&()+,\-./:;?\[\]{{}}][^\s!"()+\-/:;?\[\]{{}}]*[^\s!"()+,\-./:;?\[\]{{}}®™]'))
                          .format(numeric_re=r'(?:\d+|\d{{1,3}}(?:,\d{{3}})+)(?:(\.|,)\d+)?'))
              .finditer,
            partial(map, re.Match.group))


def zipapply(functions: Iterable[Callable], arguments: Iterable) -> Iterable:
    return map(apply, functions, arguments)
