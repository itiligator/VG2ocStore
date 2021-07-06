import mysql.connector.connection
import logging
import time


class Category:
    def __init__(self, name: str, parent: 'Category', connection: mysql.connector.connection.MySQLConnection):
        logging.debug("Category initialization")
        self.name = name
        logging.debug('Name set to ' + self.name)
        if parent:
            self.parent = parent
            logging.debug('Parent set to ' + self.parent.name)
        else:
            self.parent = None
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

    # ищет в БД категорию с таким же именем и id родительской категории
    # если не находит, то создаёт категорию в БД
    # по итогу записывает ID категории в self.ID
    def SyncWithDB(self):
        if not self._ID:
            logging.debug('Sync with DB')
            try:
                self._ID = self._fetchIDfromDB()
            except ValueError:
                self._ID = self._createCategory()

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
            search_query += " AND category.parent_id = '" + self.parent.ID + "'"

        with self._connection.cursor() as cursor:
            cursor.execute(search_query)
            result = cursor.fetchall()
            if len(result) == 1:
                logging.debug('Found same category in DB')
                return result[0]
            else:
                raise ValueError("Получили " + str(len(result)) + " совпадений по наименованию категории " + self.name + \
                                 " и ID родительской категории")

    def _createCategory(self):
        logging.debug('Creating category with name ' + self.name)
        if self.parent and not self.parent.ID:
            self.parent.SyncWithDB()
        # вносим записи о категории в таблицы
        # category, category_description, category_to_layout, category_to_store,
        insert_query = "INSERT INTO category " \
                       "SET parent_id=" + (str(self.parent.ID) if self.parent else "0") + \
                       ", top =" + ("0" if self.parent else "1") + ", `column`=1, status=1,"\
                       " date_added='" + time.strftime('%Y-%m-%d %H:%M:%S') + "', " \
                       " date_modified='" + time.strftime('%Y-%m-%d %H:%M:%S') + "';"
        with self._connection.cursor() as cursor:
            logging.debug("Writing category data to DB")
            logging.debug("Insert query is: ")
            logging.debug(insert_query)
            cursor.execute(insert_query)
            lastid = cursor.lastrowid
            insert_query = "INSERT INTO category_description " \
                           "SET category_id=" + str(lastid) + ", language_id=1, name='" + self.name + "', description='', " \
                           "meta_title='', meta_description='', meta_keyword='', meta_h1='';" \
                           "INSERT INTO category_to_layout " \
                           "SET category_id=" + str(lastid) + ", store_id=0, layout_id=0;" \
                           "INSERT INTO category_to_store " \
                           "SET category_id=" + str(lastid) + ", store_id=0;"
            if self.parent:
                # если это не коренная категория, то вносим запись в category_path (паттерн "Closure Table")
                insert_query += "INSERT INTO category_path" \
                                "SET category_id=" + str(lastid) + ", path_id=" + str(lastid) + ", level=1;" \
                                "INSERT INTO category_path" \
                                "SET category_id=" + str(lastid) + ", path_id=" + str(self.parent.ID) + ", level=0;"
            logging.debug("Insert query is: ")
            logging.debug(insert_query)
            cursor.execute(insert_query, multi=True)
