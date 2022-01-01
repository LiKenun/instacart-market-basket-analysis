from collections import namedtuple
from dataclasses import make_dataclass
from io import StringIO
from typing import Callable
import unittest
from helpers import create_mapper, is_namedtuple_instance, read_csv, write_csv, unescape


class TestHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.csv_data = 'id,name\n' \
                       '0,A\n' \
                       '1,B\n' \
                       '2,C\n'
        cls.nonunique_sequence = [9, 8, 7, 6, 5, 4, 3, 2, 1, 10, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        cls.record_sequence = ({'id': 0, 'name': 'A'},
                               {'id': 1, 'name': 'B'},
                               {'id': 2, 'name': 'C'})
        cls.row_sequence = (['id', 'name'],
                            ['0', 'A'],
                            ['1', 'B'],
                            ['2', 'C'])
        cls.unique_sequence = [9, 8, 7, 6, 5, 4, 3, 2, 1, 10]

    def test_create_mapper(self):
        data = [*range(0, 100)]
        func = lambda x: x ** 2 - 1
        self.assertSequenceEqual([*map(func, data)], [*create_mapper(func)(data)])

    def test_is_namedtuple_instance(self):
        with self.subTest('Named tuple is named tuple'):
            Record = namedtuple('Record', ['id', 'name'])
            value = Record(0, 'A')
            self.assertTrue(is_namedtuple_instance(value))
        with self.subTest('Plain tuple is not named tuple'):
            value = (0, 'A')
            self.assertFalse(is_namedtuple_instance(value))
        with self.subTest('Dataclass is not named tuple'):
            Record = make_dataclass('Record', [('id', int), ('name', str)])
            value = Record(0, 'A')
            self.assertFalse(is_namedtuple_instance(value))
        with self.subTest('Class is not named tuple'):
            def constructor(self, id, name):
                self.id = id
                self.name = name
            Record = type('Record', (), {'__init__': constructor})
            value = Record(0, 'A')
            self.assertFalse(is_namedtuple_instance(value))
        with self.subTest('Dict is not named tuple'):
            value = {'id': 0, 'name': 'A'}
            self.assertFalse(is_namedtuple_instance(value))

    def test_read_csv(self):
        with StringIO(self.csv_data) as stream:
            self.assertSequenceEqual(self.row_sequence, tuple(read_csv(stream, ',')))

    def test_unescape(self):
        with self.subTest('Can unescape one escaped double-quote character'):
            self.assertEqual('\"', unescape(r'\"'))
        with self.subTest('Can unescape one doubly-escaped double-quote character'):
            self.assertEqual('\"', unescape(unescape(r'\\\"')))


    def test_write_csv(self):
        with self.subTest('Is callable'):
            result = type(write_csv)
            self.assertIsInstance(result, Callable)
        with self.subTest('Can write data with explicit column headings'):
            with StringIO(newline='') as buffer:
                write_csv(buffer,
                          ('id', 'name'),
                          ((0, 'A'),
                           (1, 'B'),
                           (2, 'C')),
                          delimiter=',')
                buffer.seek(0)
                self.assertEqual(self.csv_data, buffer.read())
        with self.subTest('Can write data with automatic column headings (from dicts)'):
            with StringIO(newline='') as buffer:
                write_csv(buffer,
                          None,
                          ({'id': 0, 'name': 'A'},
                           {'id': 1, 'name': 'B'},
                           {'id': 2, 'name': 'C'}),
                          delimiter=',')
                buffer.seek(0)
                self.assertEqual(self.csv_data, buffer.read())
        with self.subTest('Can write data with automatic column headings (from namedtuple instances)'):
            Record = namedtuple('Record', ['id', 'name'])
            with StringIO(newline='') as buffer:
                write_csv(buffer,
                          None,
                          (Record(0, 'A'),
                           Record(1, 'B'),
                           Record(2, 'C')),
                          delimiter=',')
                buffer.seek(0)
                self.assertEqual(self.csv_data, buffer.read())
        with self.subTest('Can write data with automatic column headings (from dataclass instances)'):
            Record = make_dataclass('Record', [('id', int), ('name', str)])
            with StringIO(newline='') as buffer:
                write_csv(buffer,
                          None,
                          (Record(0, 'A'),
                           Record(1, 'B'),
                           Record(2, 'C')),
                          delimiter=',')
                buffer.seek(0)
                self.assertEqual(self.csv_data, buffer.read())
        with self.subTest('Can write data with automatic column headings (from class instances)'):
            def constructor(self, id, name):
                self.id = id
                self.name = name
            Record = type('Record', (), {'__init__': constructor})
            with StringIO(newline='') as buffer:
                write_csv(buffer,
                          None,
                          (Record(0, 'A'),
                           Record(1, 'B'),
                           Record(2, 'C')),
                          delimiter=',')
                buffer.seek(0)
                self.assertEqual(self.csv_data, buffer.read())


if __name__ == '__main__':
    unittest.main()
