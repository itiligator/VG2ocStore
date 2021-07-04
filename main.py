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
            show_table_query = "SELECT category.category_id, category.parent_id, category_description.name FROM `category`\
INNER JOIN `category_description` ON category.category_id = category_description.category_id WHERE category_description.name = 'Настойка'"
            cursor.execute(show_table_query)
            result = cursor.fetchall()
            for row in result:
                print(type(row))
                print(row)
                print(row[0])

except Error as e:
    logging.exception('Problem with DB connection')
