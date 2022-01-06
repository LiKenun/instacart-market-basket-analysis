from toolz import first, thread_last as thread
import unittest
from repositories import ProductRepository, SuggestionRepository
from services import *
from helpers import star


class TestServices(unittest.TestCase):
    def test_ProductLookupService(self):
        product_repository = ProductRepository('products.txt.xz')
        suggestions_repository = SuggestionRepository('suggestions.npz.xz')
        product_lookup_service = ProductLookupService(product_repository, suggestions_repository)
        products = product_repository.get_all_products()[0]
        with self.subTest('Empty basket and null query returns suggestions with no antecedent items'):
            self.assertTrue(thread(product_lookup_service.get_suggestions(),
                                   (map, lambda item: len(item['antecedent_items']) == 0),
                                   all))
        with self.subTest('Kimchi in basket suggests rice first'):
            self.assertEqual(thread({products.index('Kimchi')},
                                    product_lookup_service.get_suggestions,
                                    (map, lambda item: item['name']),
                                    first),
                             'Rice')
        with self.subTest('Query for “cheese” suggests both mozzarella and cheddar (in that order)'):
            self.assertSequenceEqual(thread(product_lookup_service.get_suggestions(query='cheese'),
                                            (map, lambda item: item['name']),
                                            tuple),
                                     ('Mozzarella Cheese', 'Cheddar Cheese'))
        with self.subTest('Query for “cheese” with bacon in the basket suggests cheddar cheese first'):
            self.assertSequenceEqual(thread(({products.index('Bacon')}, 'cheese'),
                                            (star, product_lookup_service.get_suggestions),
                                            (map, lambda item: item['name']),
                                            tuple),
                                     ('Cheddar Cheese', 'Mozzarella Cheese'))
        with self.subTest('Misspellings are forgiven'):
            self.assertEqual(thread(product_lookup_service.get_suggestions(query='bier'),
                                    (map, lambda item: item['name']),
                                    first),
                             'Beer')
        with self.subTest('Query for text that does not exist in any product names results in zero suggestions'):
            self.assertSequenceEqual(product_lookup_service.get_suggestions(query='burrito'),
                                     ())  # Sorry, friend. No burritos here!


if __name__ == '__main__':
    unittest.main()
