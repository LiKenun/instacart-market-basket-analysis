from io import StringIO
from operator import add, mul
import unittest
from helpers import *


class TestHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.csv_data = 'id,name\n' \
                       '0,A\n' \
                       '1,B\n' \
                       '2,C\n'
        cls.row_sequence = (['id', 'name'],
                            ['0', 'A'],
                            ['1', 'B'],
                            ['2', 'C'])

    def test_first(self):
        self.assertEqual(first((0, 1)), 0)

    def test_read_csv(self):
        with StringIO(self.csv_data) as stream:
            self.assertSequenceEqual(self.row_sequence, tuple(read_csv(stream, ',')))

    def test_second(self):
        self.assertEqual(second((0, 1)), 1)

    def test_star(self):
        self.assertEqual(star(mul, (3, 5)), 15)

    def test_tokenize(self):
        with self.subTest('Number something'):
            self.assertSequenceEqual(tuple(tokenize('No. 2 favorite')),
                                     ('No. 2', 'favorite'))
        with self.subTest('Something units'):
            self.assertSequenceEqual(tuple(tokenize('6" 3 pound item')),
                                     ('6"', '3 pound', 'item'))
        with self.subTest('Other delimited tokens'):
            self.assertSequenceEqual(tuple(tokenize('Apples, bananas, and carrots are great!')),
                                     ('Apples', 'bananas', 'and', 'carrots', 'are', 'great'))

    def text_zipapply(self):
        self.assertEqual(zipapply((sum, max), (3, 5)), (8, 5))


if __name__ == '__main__':
    unittest.main()
