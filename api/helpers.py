from ast import literal_eval
import csv
from dataclasses import astuple, fields, is_dataclass
from functools import partial
import html
from io import TextIOBase, TextIOWrapper
from itertools import groupby, starmap, zip_longest
import lzma
from lzma import LZMAFile
from operator import ne
from toolz import apply, drop, identity, peek
from typing import Any, Callable, IO, Iterable, Optional, Protocol, Sequence, Type, TypeVar

T = TypeVar('T')
U = TypeVar('U')


class SupportsLessThan(Protocol):
    def __lt__(self, __other: Any) -> bool: ...


def _write_csv_to_text_stream(file: TextIOBase, column_names: Optional[Iterable], data: Any, delimiter: str = '\t') \
        -> None:
    writer = csv.writer(file, dialect=csv.unix_dialect, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL)
    if column_names is None:
        first_row, iterator = peek(data)
        if isinstance(first_row, dict):
            column_names = first_row.keys()
            rows = (map(row.get, column_names) for row in iterator)
        elif is_dataclass(first_row):
            column_names = (field.name for field in fields(first_row))
            rows = map(astuple, iterator)
        elif is_namedtuple_instance(first_row):
            column_names = first_row._fields
            rows = iterator
        elif isinstance(first_row, Iterable):
            column_names = first_row
            rows = iterator
        else:
            column_names = tuple(vars(first_row).keys())
            rows = (map(partial(getattr, row), column_names) for row in iterator)
    else:
        rows = data
    writer.writerow(column_names)
    writer.writerows(rows)


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


def create_mapper(func: Callable, *args: Any, **kwargs: Any) -> Callable[[Iterable], Iterable]:
    if args or kwargs:
        return partial(map, partial(func, *args, **kwargs))
    else:
        return partial(map, func)


def create_sorter(key: Optional[Callable[[T], SupportsLessThan]] = None, reverse: bool = False) \
        -> Callable[[Iterable], list[T]]:
    return partial(sorted, key=key, reverse=reverse)


def first(sequence: Sequence[T]) -> T:
    return sequence[0]


def is_namedtuple_instance(value: Any) -> bool:
    return (isinstance(value, tuple) and
            hasattr(value, '_fields') and
            isinstance(value._fields, tuple) and
            all(type(item) == str for item in value._fields))


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


def read_txt(file: IO[bytes] | str | TextIOBase) -> Iterable[str]:
    with open(file, encoding='utf-8') as stream:
        for line in stream:
            yield line.rstrip()


def second(sequence: Sequence[T]) -> T:
    return sequence[1]


def unescape(value: str) -> str:
    return html.unescape(literal_eval(f'"{value}"'))


def write_compressed_csv(file: IO[bytes] | str, column_names: Optional[Iterable], data: Any, delimiter: str = '\t') \
        -> None:
    with LZMAFile(file, 'wb', format=lzma.FORMAT_XZ, check=lzma.CHECK_SHA256, preset=lzma.PRESET_EXTREME) as stream:
        write_csv(stream, column_names, data, delimiter)


def write_compressed_txt(file: IO[bytes] | str, data: Iterable[str]) -> None:
    with LZMAFile(file, 'wb', format=lzma.FORMAT_XZ, check=lzma.CHECK_SHA256, preset=lzma.PRESET_EXTREME) as stream, \
         TextIOWrapper(stream, encoding='utf-8', newline='\n') as text_stream:
        text_stream.writelines(map(lambda line: line + '\n', data))


def write_csv(file: IO[bytes] | str | TextIOBase, column_names: Optional[Iterable], data: Any, delimiter: str = '\t') \
        -> None:
    if isinstance(file, TextIOBase):
        _write_csv_to_text_stream(file, column_names, data, delimiter)
    else:
        if isinstance(file, str):
            with open(file, 'wt', encoding='utf-8', newline='') as stream:
                write_csv(stream, column_names, data)
        else:
            with TextIOWrapper(file, encoding='utf-8', newline='') as stream:
                write_csv(stream, column_names, data)


def zipapply(functions: Iterable[Callable], arguments: Iterable) -> Iterable:
    return map(apply, functions, arguments)
