import unittest
from models import Product, Rule
from repositories import ProductRepository, RulesRepository


class TestRepositories(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.products = products = {1: Product(1, 'Bacon'),
                                   2: Product(2, 'Egg'),
                                   3: Product(3, 'Cheese'),
                                   4: Product(4, 'Fish'),
                                   5: Product(5, 'Bread')}
        cls.rules = {Rule(base=(), additional=(products[1],),
                          joint_count=20234, base_count=33819106, additional_count=20234, transaction_count=33819106),
                     Rule(base=(), additional=(products[2],),
                          joint_count=75233, base_count=33819106, additional_count=75233, transaction_count=33819106),
                     Rule(base=(), additional=(products[3],),
                          joint_count=1229, base_count=33819106, additional_count=1229, transaction_count=33819106),
                     Rule(base=(), additional=(products[4],),
                          joint_count=6569, base_count=33819106, additional_count=6569, transaction_count=33819106),
                     Rule(base=(), additional=(products[5],),
                          joint_count=590, base_count=33819106, additional_count=590, transaction_count=33819106),
                     Rule(base=(products[1],), additional=(products[2],),
                          joint_count=158, base_count=33819106, additional_count=158, transaction_count=33819106),
                     Rule(base=(products[2],), additional=(products[3],),
                          joint_count=70076, base_count=33819106, additional_count=70076, transaction_count=33819106),
                     Rule(base=(products[3],), additional=(products[4],),
                          joint_count=2517, base_count=33819106, additional_count=2517, transaction_count=33819106),
                     Rule(base=(products[4],), additional=(products[5],),
                          joint_count=786, base_count=33819106, additional_count=786, transaction_count=33819106),
                     Rule(base=(products[5],), additional=(products[1],),
                          joint_count=2196, base_count=33819106, additional_count=2196, transaction_count=33819106),
                     Rule(base=(products[1], products[2]), additional=(products[3], products[4]),
                          joint_count=51738, base_count=33819106, additional_count=51738, transaction_count=33819106),
                     Rule(base=(products[1], products[3]), additional=(products[2], products[4]),
                          joint_count=2498, base_count=33819106, additional_count=2498, transaction_count=33819106),
                     Rule(base=(products[1], products[4]), additional=(products[2], products[3]),
                          joint_count=54094, base_count=33819106, additional_count=54094, transaction_count=33819106),
                     Rule(base=(products[1], products[5]), additional=(products[3], products[4]),
                          joint_count=251705, base_count=33819106, additional_count=251705, transaction_count=33819106),
                     Rule(base=(products[2], products[3]), additional=(products[1], products[4]),
                          joint_count=17462, base_count=33819106, additional_count=17462, transaction_count=33819106)}
        cls.product_repository = ProductRepository('test_products.csv.xz')
        cls.rules_repository = RulesRepository(cls.product_repository, 'test_rules.csv.xz')

    def test_get_all_products(self):
        expected = set(self.products.values())
        actual = self.product_repository.get_all_products()
        self.assertSetEqual(expected, actual)

    def test_get_all_rules(self):
        expected = self.rules
        actual = self.rules_repository.get_all_rules()
        self.assertSetEqual(expected, actual)
