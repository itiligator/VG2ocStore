import logging
import re
import json
import collections
from mysql.connector import connect, Error
from opencart_import import Category, AttributeGroup, Attribute


logging.basicConfig(filename='importer.log', level=logging.DEBUG)


try:
    with open('config.php', 'r') as config_file:
        config = {}
        DBConfig = re.compile(r"\s*define\s*\(\s*'(?P<key>.*?)'\s*,\s*'(?P<val>.*?)'\);")
        for line in config_file:
            match = DBConfig.match(line)
            if match:
                config[match.groupdict()['key']] = match.groupdict()['val']

except FileNotFoundError:
    logging.exception('Problem with config.php file')

#
# try:
#     with connect(
#         host=config['DB_HOSTNAME'],
#         user=config['DB_USERNAME'],
#         password=config['DB_PASSWORD'],
#         database=config['DB_PREFIX']+config['DB_DATABASE']
#     ) as connection:
#         # test_cat = Category("Вино", None, connection)
#         # print(test_cat.ID)
#         # test_cat2 = Category("Столовое", test_cat, connection)
#         # print(test_cat2.ID)
#         test_attr_group = AttributeGroup("Вино", connection)
#         print(test_attr_group.ID)
#         test_attr = Attribute("Тестовый", test_attr_group, connection)
#         print(test_attr.ID)
#
# except Error as e:
#     logging.exception('Problem with DB connection')

with open("log.txt", 'r', encoding='utf-8') as f:
    dd = json.load(f)

type(dd)
print(dd[0])
codes = [t['article'] for t in dd]
y=collections.Counter(codes)
print([i for i in y if y[i]>1])