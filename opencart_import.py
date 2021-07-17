import mysql.connector.connection
import logging
import time
from datetime import datetime
from pathlib import Path
import os


class OpencartObject:
    def __init__(self, name, connection):
        self.name = name
        logging.debug('Name set to ' + self.name)
        self._ID = None
        self._connection = connection
        logging.debug('Connection set to ' + repr(self._connection))

    @property
    def ID(self):
        if self._ID is not None:
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
        logging.debug('Sync with DB')
        try:
            self._ID = self._fetchIDfromDB()
            self._updateObject()
        except ValueError:
            self._ID = self._createObject()

    def _fetchIDfromDB(self):
        raise NotImplementedError

    def _createObject(self):
        raise NotImplementedError

    def _updateObject(self):
        raise NotImplementedError


class Category(OpencartObject):

    def __init__(self, name: str, parent: 'Category', connection: mysql.connector.connection.MySQLConnection):
        logging.debug("Category initialization")
        super().__init__(name, connection)
        if parent is not None:
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
                raise ValueError("Can't find category '" + self.name + "' with specified parent category ")


    def _createObject(self):
        logging.debug('Creating category with name ' + self.name)
        if self.parent is not None and self.parent.ID is None:
            self.parent.SyncWithDB()
        # вносим записи о категории в таблицы
        # category, category_description, category_to_layout, category_to_store,
        with self._connection.cursor() as cursor:
            try:
                logging.debug("Writing category data to DB")
                logging.debug("Insert query is: ")
                insert_query = "INSERT INTO category " \
                               "SET parent_id=" + (str(self.parent.ID) if self.parent is not None else "0") + \
                               ", top=" + ("0" if self.parent is not None else "1") + ", `column`=1, status=1," \
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
                               ("1" if self.parent is not None else "0") + ";"
                logging.debug("Insert query is: ")
                logging.debug(insert_query)
                cursor.execute(insert_query)

                if self.parent is not None:
                    insert_query = "INSERT INTO category_path " \
                                   "SET category_id=" + str(lastid) + ", path_id=" + str(self.parent.ID) + ", level=0;"
                    logging.debug("Insert query is: ")
                    logging.debug(insert_query)
                    cursor.execute(insert_query)

                return lastid
            except mysql.connector.Error:
                logging.exception("Something went wrong during creating category " + self.name)

    def _updateObject(self):
        logging.debug('Updating category with name ' + self.name)
        if self.parent is not None and self.parent.ID is None:
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
                               " WHERE category_id=" + str(self.ID) + ";"
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
                raise ("Can't find category group '" + self.name + "'")

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

    def _updateObject(self):
        pass  # nothing to update in AttributeGroup


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

    def _updateObject(self):
        pass  # nothing to update in Attribute


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
            'name': options['name'].replace("'", '"'),
            'price': options['price'],
        }

        if options['sale'] == 1:
            if isinstance(options['end_date'], str):
                saledate = '0000-00-00'
            else:
                saledate = datetime.utcfromtimestamp(options['end_date']).strftime('%Y-%m-%d')
            result['sale'] = {
                "sale_price": options['sale_price'],
                "date_end": saledate
            }
        else:
            result['sale'] = None

        categories = {'secondary': self.cat(options['category']).ID,
                      'main': self.cat((options["type"], options['category'])).ID}

        attributes = {}

        if options['capacity'] != 0:
            attributes[self.capacity.ID] = options['capacity']

        if options['sturdiness'] != 0:
            strud = str(options['sturdiness']).replace("%", "") + "%"
            attributes[self.sturdiness.ID] = strud

        if options['country'] != '':
            attributes[self.country.ID] = options['country']

        if options['taste'] != '':
            attributes[self.taste.ID] = options['taste']

        if options['color'] != '':
            attributes[self.color.ID] = options['color']

        result['categories'] = categories
        result['attributes'] = attributes

        result['quantity'] = options['residue_avangard']
        # for key, val in options.items():
        #     if key.isdigit():
        #         result['quantity'] += val

        result['GUID'] = options['GUID']

        return result


class Product(OpencartObject):
    def __init__(self, name, options, connection):
        logging.debug("Attribute initialization")
        self._options = options
        super().__init__(name, connection)

    def _fetchIDfromDB(self):
        search_query = "SELECT product.product_id" \
                       " FROM `product`" \
                       " WHERE product.model=" + str(self._options['model']) + \
                       " AND product.sku='" + str(self._options['sku']) + "'"

        with self._connection.cursor() as cursor:
            logging.debug(search_query)
            cursor.execute(search_query)
            result = cursor.fetchall()
            if len(result) != 0:
                logging.debug('Found same product in DB')
                return result[0][0]
            else:
                raise ValueError("Не нашли совпадений по коду " + self._options['model'] + " и артикулу "
                                                                                         + self._options['sku'])

    def _writeAttributes(self, idx):
        with self._connection.cursor() as cursor:
            for attr_id, attr_val in self._options['attributes'].items():
                insert_query = "INSERT INTO product_attribute" \
                               " SET product_id=" + str(idx) + ", " \
                               " attribute_id=" + str(attr_id) + ", " \
                               " language_id=1, " \
                               " text='" + str(attr_val) + "'"
                logging.debug(insert_query)
                cursor.execute(insert_query)

    def _writeCategories(self, idx):
        with self._connection.cursor() as cursor:
            insert_query = "INSERT INTO product_to_category " \
                           " SET product_id=" + str(idx) + ", " \
                           " category_id=" + str(self._options['categories']['main']) + ', ' \
                           " main_category=1"
            logging.debug(insert_query)
            cursor.execute(insert_query)

            insert_query = "INSERT INTO product_to_category " \
                           " SET product_id=" + str(idx) + ", " \
                           " category_id=" + str(self._options['categories']['secondary']) + ', ' \
                           " main_category=0"
            logging.debug(insert_query)
            cursor.execute(insert_query)

    def _writeSpetial(self, idx):
        if self._options['sale'] is not None:
            with self._connection.cursor() as cursor:
                insert_query = "INSERT INTO product_special " \
                               " SET product_id=" + str(idx) + ", " \
                               " customer_group_id=1, priority=0, " \
                               " price=" + str(self._options['sale']['sale_price']) + ", " \
                               " date_start='0000-00-00', date_end='" + self._options['sale']['date_end'] + "'"
                logging.debug(insert_query)
                cursor.execute(insert_query)

    def _clearStuff(self, idx):
        with self._connection.cursor() as cursor:
            try:
                delete_query = "DELETE FROM product_attribute WHERE product_id=" + str(idx)
                logging.debug(delete_query)
                cursor.execute(delete_query)
                delete_query = "DELETE FROM product_to_category WHERE product_id=" + str(idx)
                logging.debug(delete_query)
                cursor.execute(delete_query)
                delete_query = "DELETE FROM product_special WHERE product_id=" + str(idx)
                logging.debug(delete_query)
                cursor.execute(delete_query)

            except mysql.connector.Error:
                logging.exception("Something went wrong during clearing product stuff "
                                  + ', 1C code ' + self._options['model'])

    def _updateImage(self, idx, one_c_code):
        with self._connection.cursor() as cursor:
            try:
                basedir = "/vg/storage/image"
                imagefile = "/catalog/goods/product_" + str(one_c_code) + "_01.png"
                imagefullpath = basedir + imagefile
                logging.debug(imagefullpath)
                if not Path(imagefullpath).is_file():
                    imagefile = ''

                update_query = "UPDATE product" \
                               " SET image='" + imagefile + "' " \
                               " WHERE product_id=" + str(idx)

                logging.debug(update_query)
                cursor.execute(update_query)

            except mysql.connector.Error:
                logging.exception("Something went wrong during updating image"
                                  + ', 1C code ' + str(self._options['model']))

    def _createObject(self):
        logging.debug('Creating product ' + self._options['name'] + ', код ' + self._options['model'])
        # вносим записи о товаре в таблицы
        # product, product_description, product_to_layout, product_to_store
        with self._connection.cursor() as cursor:
            try:
                insert_query = "INSERT INTO product" \
                               " SET model=" + str(self._options['model']) + ", " \
                               " sku='" + str(self._options['sku']) + "', " \
                               " upc='', ean='', jan='', isbn='', mpn='', location='', " \
                               " quantity=" + str(self._options['quantity']) + ", stock_status_id=5, " \
                               " manufacturer_id=0, image=''" \
                               " shipping=1, options_buy=0, price=" + str(self._options['price']) + ", " \
                               " points=0, tax_class_id=0, " \
                               " date_available='" + time.strftime('%Y-%m-%d') + "', " \
                               " weight=0, weight_class_id=1, length=0, width=0, height=0, length_class_id=1, " \
                               " subtract=1, minimum=1, sort_order=1, status=1, viewed=1, " \
                               " date_added='" + time.strftime('%Y-%m-%d %H:%M:%S') + "', " \
                               " date_modified='" + time.strftime('%Y-%m-%d %H:%M:%S') + "', noindex=0"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                lastid = cursor.lastrowid

                insert_query = "INSERT INTO product_to_1c" \
                               " SET product_id=" + str(lastid) + ", " \
                               " 1c_id='" + self._options['GUID'] + "'"
                logging.debug(insert_query)
                cursor.execute(insert_query)
                self._connection.commit()

                insert_query = "INSERT INTO product_description" \
                               " SET product_id=" + str(lastid) + ", " \
                               " language_id=1, " \
                               " name='" + self._options['name'] + "', " \
                               " description='', short_description='', tag='', meta_title='', meta_description='', " \
                               " meta_keyword='', meta_h1=''"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                self._clearStuff(self.ID)

                self._writeCategories(lastid)
                self._writeAttributes(lastid)
                self._writeSpetial(lastid)
                self._updateImage(lastid, self._options['model'])

                insert_query = "INSERT INTO product_to_layout" \
                               " SET product_id=" + str(lastid) + ", " \
                               " store_id=0, layout_id=0"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                insert_query = "INSERT INTO product_to_store" \
                               " SET product_id=" + str(lastid) + ", " \
                               " store_id=0"
                logging.debug(insert_query)
                cursor.execute(insert_query)

                return lastid

            except mysql.connector.Error:
                logging.exception("Something went wrong during creating product "
                                  + self._options['name'] + ', 1C code ' + self._options['model'])

    def _updateObject(self):
        logging.debug('Updating product ' + self._options['name'] + ', код ' + self._options['model'])
        # вносим изменения в записи о товаре в таблицы
        # product, product_description
        with self._connection.cursor() as cursor:
            try:
                update_query = "UPDATE product " \
                               " SET status=1, noindex=0, " \
                               " sku='" + str(self._options['sku']) + "', " \
                               " quantity=" + str(self._options['quantity']) + ", " \
                               " price=" + str(self._options['price']) + ", " \
                               " date_available='" + time.strftime('%Y-%m-%d') + "', " \
                               " date_modified='" + time.strftime('%Y-%m-%d %H:%M:%S') + "' " \
                               " WHERE product_id=" + str(self.ID) + ";"
                logging.debug(update_query)
                cursor.execute(update_query)

                insert_query = "UPDATE product_description " \
                               " SET name='" + self._options['name'] + "' " \
                               " WHERE product_id=" + str(self.ID) + " "
                logging.debug(insert_query)
                cursor.execute(insert_query)

                self._clearStuff(self.ID)

                self._writeCategories(self.ID)
                self._writeAttributes(self.ID)
                self._writeSpetial(self.ID)
                self._updateImage(self.ID, self._options['model'])


            except mysql.connector.Error:
                logging.exception("Something went wrong during updating product "
                                  + self._options['name'] + ', 1C code ' + self._options['model'])

    def updateOptions(self, options):
        self._options = options
        self._ID = None

