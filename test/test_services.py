import unittest
from repositories import *
from services import *


class TestServices(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lemmatizer_service = LemmatizerService()

    def test_LemmatizerService(self):
        pass


if __name__ == '__main__':
    unittest.main()
