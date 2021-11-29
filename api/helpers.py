from ast import literal_eval
import csv
import dacite
from dacite import from_dict
from dataclasses import astuple, fields, is_dataclass
from functools import partial
from io import TextIOBase, TextIOWrapper
from itertools import starmap
import lzma
from lzma import LZMAFile
from toolz import apply, first, identity, peek, thread_last
from typing import Any, Callable, IO, Iterable, Optional, Type, TypeVar, Union

T = TypeVar('T')


def __write_csv_to_text_stream(file: TextIOBase, column_names: Optional[Iterable], data: Any) -> None:
    writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL, dialect=csv.unix_dialect)
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
            column_names = tuple(map(first, vars(first_row).items()))
            rows = (map(partial(getattr, row), column_names) for row in iterator)
    else:
        rows = data
    writer.writerow(column_names)
    writer.writerows(rows)


def create_dict_to_dataclass_mapper(data_class: Type[T], config: Optional[dacite.Config] = None) -> Callable[[Iterable[dict[str, Any]]], Iterable[T]]:
    def function(iterable: Iterable[dict[str, Any]]) -> Iterable[T]:
        return map(partial(from_dict, data_class, config=config), iterable)
    return function


def create_mapper(func: Callable) -> Callable[[Iterable], Iterable]:
    return partial(map, func)


def create_transform(transformations: dict[str, Callable]) -> Callable[[Iterable[list[str]]], Iterable[dict]]:
    return partial(transform, transformations)


def is_namedtuple_instance(value: Any) -> bool:
    return (isinstance(value, tuple) and
            hasattr(value, '_fields') and
            isinstance(value._fields, tuple) and
            all(type(item) == str for item in value._fields))


def read_compressed_csv(file: Union[IO[bytes], str]) -> Iterable[list[str]]:
    with lzma.open(file, 'rt', format=lzma.FORMAT_XZ, encoding='utf-8') as stream:
        for row in read_csv(stream):
            yield row


def read_csv(file: Union[IO[bytes], str, TextIOBase]) -> Iterable[list[str]]:
    if isinstance(file, TextIOBase):
        for row in csv.reader(file):
            yield row
    else:
        create_stream = open if isinstance(file, str) else TextIOWrapper
        with create_stream(file, encoding='utf-8') as stream:
            for row in csv.reader(stream):
                yield row


def transform(transformations: dict[str, Callable], data: Iterable[list[str]]) -> Iterable[dict]:
    iterator = iter(data)
    column_names = next(iterator)
    transformation_list = tuple(transformations.get(column_name, identity)
                                for column_name in column_names)
    for row in iterator:
        yield thread_last(row,
                          (zip, transformation_list),
                          (starmap, apply),
                          (zip, column_names),
                          dict)


def unescape(value: str) -> str:
    return literal_eval(f'"{value}"')


# By Raymond Hettinger (https://twitter.com/raymondh/status/944125570534621185)
# See also: https://www.peterbe.com/plog/fastest-way-to-uniquify-a-list-in-python-3.6
def unique(iterable: Iterable) -> list:
    return list(dict.fromkeys(iterable))


def write_compressed_csv(file: Union[IO[bytes], str], column_names: Optional[Iterable], data: Any) -> None:
    with LZMAFile(file, 'wb', format=lzma.FORMAT_XZ, check=lzma.CHECK_SHA256, preset=lzma.PRESET_EXTREME) as stream:
        write_csv(stream, column_names, data)


def write_csv(file: Union[IO[bytes], str, TextIOBase], column_names: Optional[Iterable], data: Any) -> None:
    if isinstance(file, TextIOBase):
        __write_csv_to_text_stream(file, column_names, data)
    else:
        if isinstance(file, str):
            with open(file, 'wt', encoding='utf-8', newline='') as stream:
                write_csv(stream, column_names, data)
        else:
            with TextIOWrapper(file, encoding='utf-8', newline='') as stream:
                write_csv(stream, column_names, data)
