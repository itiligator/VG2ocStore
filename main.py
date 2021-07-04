import logging
import re
from mysql.connector import connect, Error

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


try:
    with connect(
        host=config['DB_HOSTNAME'],
        user=config['DB_USERNAME'],
        password=config['DB_PASSWORD'],
        database=config['DB_PREFIX']+config['DB_DATABASE']
    ) as connection:
        print(connection)
        with connection.cursor() as cursor:
            show_table_query = "DESCRIBE product"
            cursor.execute(show_table_query)
            for db in cursor:
                print(db)
except Error as e:
    logging.exception('Problem with DB connection')
