import numpy as np
from toolz import thread_last as thread
import unittest
from models import *


class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.suggestion_data = \
            (np.array([ 9, 25, 3,  7, 8, 10], dtype=np.uint32),
             np.array([35, 25, 2,  7, 6, 10], dtype=np.uint32),
             np.array([28, 25, 2,  7, 6, 10], dtype=np.uint32),
             np.array([10, 25, 2,  6, 7, 35], dtype=np.uint32),
             np.array([10, 25, 2,  6, 7, 28], dtype=np.uint32),
             np.array([ 9, 25, 8, 25, 8], dtype=np.uint32),
             np.array([10, 25, 7, 25, 7], dtype=np.uint32),
             np.array([35, 25, 6, 25, 6], dtype=np.uint32),
             np.array([28, 25, 6, 25, 6], dtype=np.uint32),
             np.array([34, 25, 5, 25, 5], dtype=np.uint32))
        cls.suggestion_properties = \
            ({'antecedent_count': 7, 'antecedent_items': (10,), 'consequent_count': 8, 'consequent_item': 9,
              'item_set_count': 3, 'lift': 25 * 3 / (7 * 8), 'support': 3 / 25, 'transaction_count': 25},
             {'antecedent_count': 7, 'antecedent_items': (10,), 'consequent_count': 6, 'consequent_item': 35,
              'item_set_count': 2, 'lift': 25 * 2 / (7 * 6), 'support': 2 / 25, 'transaction_count': 25},
             {'antecedent_count': 7, 'antecedent_items': (10,), 'consequent_count': 6, 'consequent_item': 28,
              'item_set_count': 2, 'lift': 25 * 2 / (7 * 6), 'support': 2 / 25, 'transaction_count': 25},
             {'antecedent_count': 6, 'antecedent_items': (35,), 'consequent_count': 7, 'consequent_item': 10,
              'item_set_count': 2, 'lift': 25 * 2 / (6 * 7), 'support': 2 / 25, 'transaction_count': 25},
             {'antecedent_count': 6, 'antecedent_items': (28,), 'consequent_count': 7, 'consequent_item': 10,
              'item_set_count': 2, 'lift': 25 * 2 / (6 * 7), 'support': 2 / 25, 'transaction_count': 25},
             {'antecedent_count': 25, 'antecedent_items': (), 'consequent_count': 8, 'consequent_item': 9,
              'item_set_count': 8, 'lift': 1.0, 'support': 8 / 25, 'transaction_count': 25},
             {'antecedent_count': 25, 'antecedent_items': (), 'consequent_count': 7, 'consequent_item': 10,
              'item_set_count': 7, 'lift': 1.0, 'support': 7 / 25, 'transaction_count': 25},
             {'antecedent_count': 25, 'antecedent_items': (), 'consequent_count': 6, 'consequent_item': 35,
              'item_set_count': 6, 'lift': 1.0, 'support': 6 / 25, 'transaction_count': 25},
             {'antecedent_count': 25, 'antecedent_items': (), 'consequent_count': 6, 'consequent_item': 28,
              'item_set_count': 6, 'lift': 1.0, 'support': 6 / 25, 'transaction_count': 25},
             {'antecedent_count': 25, 'antecedent_items': (), 'consequent_count': 5, 'consequent_item': 34,
              'item_set_count': 5, 'lift': 1.0, 'support': 5 / 25, 'transaction_count': 25})

    def test_Suggestion(self):
        with self.subTest('Suggestions constructed from NumPy arrays have expected properties'):
            for suggestion, properties in zip(map(Suggestion, self.suggestion_data), self.suggestion_properties):
                with self.subTest(f'Suggestion constructed from {suggestion.data} has expected properties'):
                    self.assertTrue(all(getattr(suggestion, property_name) == properties[property_name]
                                        for property_name in properties))
        with self.subTest('Sorted sequence of suggestions in descending order of lift, then support and product'):
            self.assertSequenceEqual(thread(self.suggestion_data,
                                            (map, Suggestion),
                                            sorted,
                                            (map, lambda suggestion: suggestion.data),
                                            tuple),
                                     thread(range(10),  # It was already sorted to begin with, so the indices match.
                                            (map, self.suggestion_data.__getitem__),
                                            tuple))


if __name__ == '__main__':
    unittest.main()
