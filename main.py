import logging
import re
import json
import os
from mysql.connector import connect, Error
from opencart_import import Product, ProductOptions


logging.basicConfig(filename='importer.log', level=logging.INFO, encoding='utf-8')


def import_to_db(catalog):
    try:
        config_filename = os.getcwd() + "/master/config.php"
        with open(config_filename, 'r') as config_file:
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
            pr_opt = ProductOptions(connection=connection)
            pr = Product(options=pr_opt.generate(catalog[0]), connection=connection, name='')
            l=len(catalog)
            logging.info("Start importing " + str(l) + " goods from catalog")

            with connection.cursor() as cursor:
                try:
                    update_query = "UPDATE `product` SET status=0"
                    logging.debug(update_query)
                    cursor.execute(update_query)
                except Error:
                    logging.exception("Something went wrong during setting status to 0")

            for good in catalog:
                pr.updateOptions(pr_opt.generate(good))
                pr.SyncWithDB()

            logging.info("Import Finished")

    except Error as e:
        logging.exception('Problem with DB connection')
