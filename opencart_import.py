import mysql.connector.connection
import logging
import time
from datetime import datetime


class OpencartObject:
    def __init__(self, name, connection):
        self.name = name
        logging.debug('Name set to ' + self.name)
        self._ID = None
        self._connection = connection
        logging.debug('Connection set to ' + repr(self._connection))

    @property
    def ID(self):
        if self._ID:
            return self._ID
        else:
            self.SyncWithDB()
            return self._ID

    @ID.setter
    def ID(self, ID):
        raise AttributeError("Cannot modify ID")

    # ищет в БД объект
    # если находит, то обновляет поля объекта в БД
    # если не находит, то создаёт объект в БД
    # по итогу записывает ID категории в self.ID
    def SyncWithDB(self):
        if not self._ID:
            logging.debug('Sync with DB')
            try:
                self._ID = self._fetchIDfromDB()
                self._updadeObject()
            except ValueError:
                self._ID = self._createObject()

    def _fetchIDfromDB(self):
        raise NotImplementedError

    def _createObject(self):
        raise NotImplementedError

    def _updadeObject(self):
        raise NotImplementedError


class Category(OpencartObject):

    def __init__(self, name: str, parent: 'Category', connection: mysql.connector.connection.MySQLConnection):
        logging.debug("Category initialization")
        super().__init__(name, connection)
        if parent:
            self.parent = parent
            logging.debug('Parent set to ' + self.parent.name)
        else:
            self.parent = None

    # получает ID категории из БД
    # категорию ищет по совпадению имени и ID родительской категории
    # если не находит категорию, то кидает исключение
    def _fetchIDfromDB(self):
        search_query = "SELECT category.category_id \
                        FROM `category`\
                        INNER JOIN `category_description` \
                        ON category.category_id = category_description.category_id \
                        WHERE category_description.name = '" + self.name + "'"
        if self.parent is not None:
            search_query += " AND category.parent_id = '" + str(self.parent.ID) + "'"

        with self._connection.cursor() as cursor:
            cursor.execute(search_query)
            result = cursor.fetchall()
            if len(result) != 0:
                logging.debug('Found same category in DB')
                return result[0][0]
            else:
                raise ValueError("Не нашли совпадений по наименованию категории " + self.name + "и ID родительской "
                                                                                                "категории")

    def _createObject(self):
        logging.debug('Creating category with name ' + self.name)
        if self.parent and not self.parent.ID:
            self.parent.SyncWithDB()
        # вносим записи о категории в таблицы
        # category, category_description, category_to_layout, category_to_store,
        with self._connection.cursor() as cursor:
            try:
                logging.debug("Writing category data to DB")
                logging.debug("Insert query is: ")
                insert_query = "INSERT INTO category " \
                               "SET parent_id=" + (str(self.parent.ID) if self.parent else "0") + \
                               ", top=" + ("0" if self.parent else "1") + ", `column`=1, status=1," \
                               " date_added='" + time.strftime('%Y-%m-%d %H:%M:%S') + "', " \
                               " date_modified='" + time.strftime('%Y-%m-%d %H:%M:%S') + "';"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                lastid = cursor.lastrowid

                insert_query = "INSERT INTO category_description " \
                               "SET category_id=" + str(lastid) + ", language_id=1, name='" + self.name + "', " \
                               "description='', meta_title='', meta_description='', meta_keyword='', meta_h1='';"
                logging.debug("Insert query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                insert_query = "INSERT INTO category_to_layout " \
                               "SET category_id=" + str(lastid) + ", store_id=0, layout_id=0;"
                logging.debug("Insert query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                insert_query = "INSERT INTO category_to_store " \
                               "SET category_id=" + str(lastid) + ", store_id=0;"
                logging.debug("Insert query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                insert_query = "INSERT INTO category_path " \
                               "SET category_id=" + str(lastid) + ", path_id=" + str(lastid) + ", level=" + \
                               ("1" if self.parent else "0") + ";"
                logging.debug("Insert query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                if self.parent:
                    insert_query = "INSERT INTO category_path " \
                                   "SET category_id=" + str(lastid) + ", path_id=" + str(self.parent.ID) + ", level=0;"
                    logging.debug("Insert query is: ")
                    logging.debug(insert_query)
                    cursor.execute(insert_query)

                return lastid
            except mysql.connector.Error:
                logging.exception("Something went wrong during creating category " + self.name)

    def _updadeObject(self):
        logging.debug('Updating category with name ' + self.name)
        if self.parent and not self.parent.ID:
            self.parent.SyncWithDB()
        # обновляем (на самом деле приовдим в порядок) записи о категории в таблицах
        # category, category_to_layout, category_to_store,
        with self._connection.cursor() as cursor:
            try:
                logging.debug("Updating category data into DB")
                logging.debug("Update query is: ")
                insert_query = "UPDATE category" \
                               " SET status=1," \
                               " date_modified='" + time.strftime('%Y-%m-%d %H:%M:%S') + "'" \
                                                                                         " WHERE category_id=" + str(
                    self.ID) + ";"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                insert_query = "UPDATE category_to_layout" \
                               " SET store_id=0, layout_id=0" \
                               " WHERE category_id=" + str(self.ID) + ";"
                logging.debug("Update query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                insert_query = "UPDATE category_to_store" \
                               " SET store_id=0" \
                               " WHERE category_id=" + str(self.ID) + ";"
                logging.debug("Update query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

            except mysql.connector.Error:
                logging.exception("Something went wrong during updating category " + self.name)


class AttributeGroup(OpencartObject):

    def __init__(self, name: str, connection: mysql.connector.connection.MySQLConnection):
        logging.debug("AttributeGroup initialization")
        super().__init__(name, connection)

    def _fetchIDfromDB(self):
        search_query = "SELECT attribute_group.attribute_group_id \
                        FROM `attribute_group`\
                        INNER JOIN `attribute_group_description` \
                        ON attribute_group.attribute_group_id = attribute_group_description.attribute_group_id \
                        WHERE attribute_group_description.name = '" + self.name + "'"

        with self._connection.cursor() as cursor:
            cursor.execute(search_query)
            result = cursor.fetchall()
            if len(result) != 0:
                logging.debug('Found same category in DB')
                return result[0][0]
            else:
                raise ValueError("Не нашли совпадений по наименованию группы категорий " + self.name)

    def _createObject(self):
        logging.debug('Creating attribute group with name ' + self.name)
        with self._connection.cursor() as cursor:
            try:
                logging.debug("Writing attribute group data to DB")
                logging.debug("Insert query is: ")
                insert_query = "INSERT INTO attribute_group " \
                               "SET sort_order=0;"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                lastid = cursor.lastrowid

                insert_query = "INSERT INTO attribute_group_description " \
                               "SET attribute_group_id=" + str(lastid) + ", language_id=1, name='" + self.name + "';"
                logging.debug("Insert query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                return lastid
            except mysql.connector.Error:
                logging.exception("Something went wrong during creating attribute group " + self.name)

    def _updadeObject(self):
        pass


class Attribute(OpencartObject):

    def __init__(self, name: str, group: AttributeGroup, connection: mysql.connector.connection.MySQLConnection):
        logging.debug("Attribute initialization")
        self._group = group
        super().__init__(name, connection)

    def _fetchIDfromDB(self):
        search_query = "SELECT attribute.attribute_id \
                        FROM `attribute`\
                        INNER JOIN `attribute_description` \
                        ON attribute.attribute_id = attribute_description.attribute_id \
                        WHERE attribute_description.name = '" + self.name + "'" \
                        " AND attribute.attribute_group_id = '" + str(self._group.ID) + "'"

        with self._connection.cursor() as cursor:
            cursor.execute(search_query)
            result = cursor.fetchall()
            if len(result) != 0:
                logging.debug('Found same category in DB')
                return result[0][0]
            else:
                raise ValueError("Не нашли совпадений по наименованию группы категорий " + self.name)

    def _createObject(self):
        logging.debug('Creating attribute group with name ' + self.name)
        with self._connection.cursor() as cursor:
            try:
                logging.debug("Writing attribute group data to DB")
                logging.debug("Insert query is: ")
                insert_query = "INSERT INTO attribute " \
                               "SET sort_order=0, attribute_group_id=" + str(self._group.ID) + ";"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                lastid = cursor.lastrowid

                insert_query = "INSERT INTO attribute_description " \
                               "SET attribute_id=" + str(lastid) + ", language_id=1, name='" + self.name + "';"
                logging.debug("Insert query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                return lastid
            except mysql.connector.Error:
                logging.exception("Something went wrong during creating attribute group " + self.name)

    def _updadeObject(self):
        pass


class ProductOptions:

    def __init__(self, connection: mysql.connector.connection.MySQLConnection):
        self.categories = {}
        self.connection = connection
        self.alco_group = AttributeGroup('Алкогольные товары', self.connection)
        self.wine_group = AttributeGroup('Вино', self.connection)

        self.capacity = Attribute('Емкость', self.alco_group, connection)
        self.sturdiness = Attribute('Крепкость', self.alco_group, connection)
        self.country = Attribute('Страна', self.alco_group, connection)

        self.color = Attribute('Цвет', self.wine_group, connection)
        self.taste = Attribute('Сахар', self.wine_group, connection)

    def cat(self, tag):
        try:
            return self.categories[tag]
        except KeyError:
            if isinstance(tag, str):
                self.categories[tag] = Category(name=tag, parent=None, connection=self.connection)
            elif isinstance(tag, tuple):
                self.categories[tag] = Category(name=tag[0], parent=self.cat(tag[1]), connection=self.connection)
            else:
                return AttributeError
            return self.categories[tag]


    def generate(self, options: dict):
        result = {
            'model': options['code'],
            'sku': options['article'],
            'name': options['name'],
            'price': options['price'],
        }

        if options['sale'] == 1:
            result['sale'] = {
                "sale_price": options['sale_price'],
                "date_end": datetime.utcfromtimestamp(options['end_date']).strftime('%Y-%m-%d %H:%M:%S')
            }
        else:
            result['sale'] = None

        categories = {'main': self.cat(options['category']).ID,
                      'secondary': self.cat((options["type"], options['category'])).ID}

        attributes = {self.capacity.ID: options['capacity'],
                      self.sturdiness.ID: options['sturdiness'],
                      self.country.ID: options['country']}

        if options['category'] == 'ВИНО':
            attributes[self.taste.ID] = options['taste']
            attributes[self.color.ID] = options['color']

        result['categories'] = categories
        result['attributes'] = attributes

        result['quantity'] = options['residue_avangard']
        for key, val in options:
            if key.isdigit():
                result['quantity'] += val


class Product(OpencartObject):
    def __init__(self, name, options, connection):
        logging.debug("Attribute initialization")
        self._options = options
        super().__init__(name, connection)

    def _fetchIDfromDB(self):
        search_query = "SELECT product.product_id" \
                       " FROM `product`" \
                       " WHERE product.model=" + str(self._options.model) + \
                       " AND product.sku=" + str(self._options.sku)

