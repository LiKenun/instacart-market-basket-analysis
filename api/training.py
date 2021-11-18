import numpy as np
import pandas as pd

data = pd.read_csv(r'D:\School\CTP\shopping-assistant\data\order_products__train.csv') \
         .append(pd.read_csv(r'D:\School\CTP\shopping-assistant\data\order_products__prior.csv')) \
         .join(pd.read_csv(r'D:\School\CTP\shopping-assistant\data\orders.csv', index_col='order_id'),
               on='order_id',
               how='inner',
               sort=True) \
         .join(pd.read_csv(r'D:\School\CTP\shopping-assistant\data\products.csv', index_col='product_id'),
               on='product_id',
               how='inner') \
         .join(pd.read_csv(r'D:\School\CTP\shopping-assistant\data\aisles.csv', index_col='aisle_id'),
               on='aisle_id',
               how='inner') \
         .join(pd.read_csv(r'D:\School\CTP\shopping-assistant\data\departments.csv', index_col='department_id'),
               on='department_id',
               how='inner')
