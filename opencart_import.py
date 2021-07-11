import mysql.connector.connection
import logging
import time


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


class Product(OpencartObject):
    pass

