from itertools import starmap
from toolz import thread_last as thread
import unittest
from models import *
from services import *


class TestServices(unittest.TestCase):
    def test_LemmatizerService(self):
        with self.subTest('tokenize'):
            with self.subTest('“apples, bananas, and carrots” tokenizes to {“apples”, “bananas”, “and”, “carrots”}'):
                self.assertSequenceEqual(tuple(LemmatizerService.tokenize('apples, bananas, and carrots')),
                                         ('apples', 'bananas', 'and', 'carrots'))
        with self.subTest('lemmatize'):
            lemmatizer_service = LemmatizerService()
            with self.subTest('“apples, bananas, and carrots” produces lemmas {“apple”, “banana”, “carrot”}'):
                self.assertSequenceEqual(tuple(lemmatizer_service.lemmatize('apples, bananas, and carrots')),
                                         (('apple', 'apples'), ('banana', 'bananas'), ('carrot', 'carrots')))

    def test_ProductLookupService(self):
        # The products are sorted in descending order (by identifier).
        # These are taken from https://www.javatpoint.com/apriori-algorithm-in-machine-learning
        products = \
            thread(('Chicken', 'Light Cream', 'Escalope', 'Mushroom Cream Sauce', 'Pasta', 'Fromage Blanc', 'Honey',
                   'Ground Beef', 'Herb & Pepper', 'Tomato Sauce', 'Olive Oil', 'Whole Wheat Pasta', 'Shrimp'),
                   enumerate,
                   (starmap, lambda index, name: Product(index, name)),
                   tuple)
        rules = \
            (Rule((),              (products[0],),  Measure(1.0,                0.004533333333333334)),
             Rule((),              (products[1],),  Measure(1.0,                0.007733333333333334)),
             Rule((),              (products[2],),  Measure(1.0,                0.0116)),
             Rule((),              (products[3],),  Measure(1.0,                0.005733333333333333)),
             Rule((),              (products[4],),  Measure(1.0,                0.005866666666666667)),
             Rule((),              (products[5],),  Measure(1.0,                0.0033333333333333335)),
             Rule((),              (products[6],),  Measure(1.0,                0.0033333333333333335)),
             Rule((),              (products[7],),  Measure(1.0,                0.021333333333333333)),
             Rule((),              (products[8],),  Measure(1.0,                0.016)),
             Rule((),              (products[9],),  Measure(1.0,                0.005333333333333333)),
             Rule((),              (products[10],), Measure(1.0,                0.0112)),
             Rule((),              (products[11],), Measure(1.0,                0.008)),
             Rule((),              (products[12],), Measure(1.0,                0.005066666666666666)),
             Rule((products[0],),  (products[1],),  Measure(4.843304843304844,  0.004533333333333334)),
             Rule((products[2],),  (products[3],),  Measure(3.7903273197390845, 0.005733333333333333)),
             Rule((products[2],),  (products[4],),  Measure(4.700185158809287,  0.005866666666666667)),
             Rule((products[4],),  (products[12],), Measure(4.514493901473151,  0.005066666666666666)),
             Rule((products[5],),  (products[6],),  Measure(5.178127589063795,  0.0033333333333333335)),
             Rule((products[7],),  (products[8],),  Measure(3.2915549671393096, 0.016)),
             Rule((products[9],),  (products[7],),  Measure(3.840147461662528,  0.005333333333333333)),
             Rule((products[10],), (products[1],),  Measure(3.120611639881417,  0.0032)),
             Rule((products[10],), (products[11],), Measure(4.130221288078346,  0.008)))
        product_lookup_service = \
            ProductLookupService(type('', (), {'products_data_file': '', 'get_all_products': (lambda _: products)})(),
                                 type('', (), {'rules_data_file': '', 'get_all_rules': (lambda _: rules)})(),
                                 LemmatizerService())
        with self.subTest('Empty basket and null query returns suggestions with no antecedent items'):
            self.assertTrue(thread(product_lookup_service.get_suggestions(),
                                   (map, lambda suggestion: suggestion.antecedent_items == ()),
                                   all))
        with self.subTest('Olive oil in basket suggests whole wheat pasta, light cream, …'):
            self.assertSequenceEqual(thread({10},
                                            product_lookup_service.get_suggestions,
                                            (map, lambda suggestion: suggestion.product.name),
                                            tuple),
                                     ('Whole Wheat Pasta', 'Light Cream', 'Ground Beef', 'Herb & Pepper', 'Escalope',
                                      'Pasta', 'Mushroom Cream Sauce', 'Tomato Sauce', 'Shrimp', 'Chicken'))
        with self.subTest('Query for “cre” suggests both light cream and mushroom cream sauce'):
            self.assertSequenceEqual(thread(product_lookup_service.get_suggestions(query='cream'),
                                            (map, lambda suggestion: suggestion.product.name),
                                            tuple),
                                     ('Light Cream', 'Mushroom Cream Sauce'))
        with self.subTest('Query for “cre” with escalope in basket suggests mushroom cream sauce and light cream'):
            self.assertSequenceEqual(thread(product_lookup_service.get_suggestions({2}, 'cre'),
                                            (map, lambda suggestion: suggestion.product.name),
                                            tuple),
                                     ('Mushroom Cream Sauce', 'Light Cream'))
        with self.subTest('Query for text that does not exist in any product names results in zero suggestions'):
            self.assertSequenceEqual(product_lookup_service.get_suggestions(query='gmijul[kfakl,kim49iklgijldvs48n5wi'),
                                     ())


if __name__ == '__main__':
    unittest.main()
