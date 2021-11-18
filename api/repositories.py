import csv
from models import *


class ProductRepository:
    @staticmethod
    def get_all_products():
        with open(r'D:\School\CTP\shopping-assistant\data\products.csv', newline='', encoding='utf-8') as file:
            rows = csv.reader(file)
            column_names = next(rows)
            id_index = column_names.index('product_id')
            name_index = column_names.index('product_name')
            for row in rows:
                yield Product(row[id_index], row[name_index])
