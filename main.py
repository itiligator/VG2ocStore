import logging
import re
import json
from mysql.connector import connect, Error
from opencart_import import Product, ProductOptions


logging.basicConfig(filename='importer.log', level=logging.DEBUG)

def import_to_db(catalog):
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


    try:
        with connect(
            host=config['DB_HOSTNAME'],
            user=config['DB_USERNAME'],
            password=config['DB_PASSWORD'],
            database=config['DB_PREFIX']+config['DB_DATABASE']
        ) as connection:
            with open("JSON.txt", 'r', encoding='utf-8-sig') as f:
                goods = json.load(f)
            pr_opt = ProductOptions(connection=connection)
            pr = Product(options=pr_opt.generate(goods[116]), connection=connection, name='')
            i = 0
            l=len(goods)

            with connection.cursor() as cursor:
                try:
                    update_query = "UPDATE `product` SET status=0"
                    logging.debug(update_query)
                    cursor.execute(update_query)
                except Error:
                    logging.exception("Something went wrong during setting status to 0")

            for good in goods:
                pr = Product(options=pr_opt.generate(good), connection=connection, name='')
                pr.SyncWithDB()
                i += 1
                print(str(i) + "/" + str(l))

    except Error as e:
        logging.exception('Problem with DB connection')
