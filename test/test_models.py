from dataclass_type_validator import TypeValidationError
from itertools import chain, starmap
from math import nan
from toolz import thread_last as thread
import unittest
from models import *


class TestModels(unittest.TestCase):
    @staticmethod
    def create_measures(*measures):
        return tuple(starmap(Measure, measures))

    @classmethod
    def setUpClass(cls):
        # The products are sorted in descending order (by identifier).
        # These are taken from https://www.javatpoint.com/apriori-algorithm-in-machine-learning
        cls.products = products = \
            thread(('Chicken', 'Light Cream', 'Escalope', 'Mushroom Cream Sauce', 'Pasta', 'Fromage Blanc', 'Honey',
                   'Ground Beef', 'Herb & Pepper', 'Tomato Sauce', 'Olive Oil', 'Whole Wheat Pasta', 'Shrimp'),
                   enumerate,
                   (starmap, lambda index, name: Product(index, name)),
                   tuple)
        cls.rules = rules = \
            (Rule((),   (0,),   Measure(1.0,                0.004533333333333334)),
             Rule((),   (1,),   Measure(1.0,                0.007733333333333334)),
             Rule((),   (2,),   Measure(1.0,                0.0116)),
             Rule((),   (3,),   Measure(1.0,                0.005733333333333333)),
             Rule((),   (4,),   Measure(1.0,                0.005866666666666667)),
             Rule((),   (5,),   Measure(1.0,                0.0033333333333333335)),
             Rule((),   (6,),   Measure(1.0,                0.0033333333333333335)),
             Rule((),   (7,),   Measure(1.0,                0.021333333333333333)),
             Rule((),   (8,),   Measure(1.0,                0.016)),
             Rule((),   (9,),   Measure(1.0,                0.005333333333333333)),
             Rule((),   (10,),  Measure(1.0,                0.0112)),
             Rule((),   (11,),  Measure(1.0,                0.008)),
             Rule((),   (12,),  Measure(1.0,                0.005066666666666666)),
             Rule((0,),  (1,),  Measure(4.843304843304844,  0.004533333333333334)),
             Rule((2,),  (3,),  Measure(3.7903273197390845, 0.005733333333333333)),
             Rule((2,),  (4,),  Measure(4.700185158809287,  0.005866666666666667)),
             Rule((4,),  (12,), Measure(4.514493901473151,  0.005066666666666666)),
             Rule((5,),  (6,),  Measure(5.178127589063795,  0.0033333333333333335)),
             Rule((7,),  (8,),  Measure(3.2915549671393096, 0.016)),
             Rule((9,),  (7,),  Measure(3.840147461662528,  0.005333333333333333)),
             Rule((10,), (1,),  Measure(3.120611639881417,  0.0032)),
             Rule((10,), (11,), Measure(4.130221288078346,  0.008)))
        cls.suggestions = \
            thread(rules,
                   (map, lambda rule: (tuple(map(products.__getitem__, rule.consequent_items)),
                                       rule.measure,
                                       tuple(map(products.__getitem__, rule.antecedent_items)))),
                   (starmap, lambda consequent_items, measure, antecedent_items:
                                 ((consequent_item, measure, antecedent_items)
                                  for consequent_item in consequent_items)),
                   chain.from_iterable,
                   (starmap, Suggestion),
                   tuple)

    def test_Measure(self):
        with self.subTest('Negative lift throws ValueError'):
            self.assertRaises(ValueError, lambda: Measure(-0.1, 0.0))
        with self.subTest('Negative support throws ValueError'):
            self.assertRaises(ValueError, lambda: Measure(0.0, -0.1))
        with self.subTest('Support greater than 1 throws ValueError'):
            self.assertRaises(ValueError, lambda: Measure(0.0, 1.1))
        with self.subTest('NaN lift throws ValueError'):
            self.assertRaises(ValueError, lambda: Measure(nan, 0.0))
        with self.subTest('NaN support throws ValueError'):
            self.assertRaises(ValueError, lambda: Measure(0.0, nan))

    def test_Product(self):
        with self.subTest('Non-integral identifier throws TypeValidationError'):
            self.assertRaises(TypeValidationError, lambda: Product(0.0, 'Proddy Product'))
        with self.subTest('Negative identifier throws ValueError'):
            self.assertRaises(ValueError, lambda: Product(-1, 'Proddy Product'))
        with self.subTest('None for name throws TypeValidationError'):
            self.assertRaises(TypeValidationError, lambda: Product(1, None))
        with self.subTest('Empty string for name throws ValueError'):
            self.assertRaises(ValueError, lambda: Product(1, ''))

    def test_Rule(self):
        with self.subTest('Unsorted antecedent products throws ValueError'):
            self.assertRaises(ValueError, lambda: Rule(tuple(range(10, 0, -1)),
                                                       (11,),
                                                       Measure(0.0, 0.0)))
        with self.subTest('Duplicate antecedent products throws ValueError'):
            self.assertRaises(ValueError, lambda: Rule((0, 1, 1),
                                                       (14,),
                                                       Measure(0.0, 0.0)))
        with self.subTest('No consequent products throws ValueError'):
            self.assertRaises(ValueError, lambda: Rule(tuple(range(10)), (), Measure(0.0, 0.0)))
        with self.subTest('Unsorted consequent products throws ValueError'):
            self.assertRaises(ValueError, lambda: Rule((), tuple(range(10, 0, -1)), Measure(0.0, 0.0)))
        with self.subTest('Duplicate consequent products throws ValueError'):
            self.assertRaises(ValueError, lambda: Rule((11,),
                                                       (0, 1, 1),
                                                       Measure(0.0, 0.0)))
        with self.subTest('Any product which is both antecedent and consequent throws ValueError'):
            self.assertRaises(ValueError, lambda: Rule(tuple(range(10)), (0,), Measure(0.0, 0.0)))

    def test_Suggestion(self):
        with self.subTest('Sorted sequence of suggestions sort in descending order of lift, then support and product'):
            self.assertSequenceEqual(thread(self.suggestions,
                                            sorted,
                                            (map, lambda suggestion: suggestion.product.identifier),
                                            tuple),
                                     (6, 1, 4, 12, 11, 7, 3, 8, 1, 7, 8, 2, 10, 11, 1, 4, 3, 9, 12, 0, 6, 5))


if __name__ == '__main__':
    unittest.main()
