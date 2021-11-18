from functools import reduce
from itertools import islice
import re
from models import *
from repositories import *


class ProductLookupService:
    __word_re = re.compile(r'[\w\d]+')

    def __init__(self):
        id_table = {}
        name_index = {}
        for product in ProductRepository.get_all_products():
            id_table[product.id] = product.name
            for word in ProductLookupService.__word_re.findall(product.name.casefold()):
                name_index.setdefault(word, set()).add(product)
        self.__id_table = id_table
        self.__name_index = name_index

    def get_name_by_id(self, id):
        return self.__id_table[id]

    def get_by_query(self, query):
        return [product.__dict__
                for product
                in islice(reduce(set.union,
                                 (self.__name_index.get(term.casefold(), set())
                                  for term
                                  in ProductLookupService.__word_re.findall(query)),
                                 set()),
                          10)]
