import mysql.connector.connection


class Category:
    def __init__(self, name: str, parent: 'Category', connection: mysql.connector.connection.MySQLConnection):
        self.name = name
        if parent:
            self.parent = parent
        else:
            self.parent = None
        self._ID = None
        self._connection = connection

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

    # ищет в БД категорию с таким же именем (description) и id родительской категории
    # если не находит, то создаёт категорию в БД
    # по итогу записывает ID категории в self.ID
    def SyncWithDB(self):
        if not self._ID:
            try:
                self._ID = self._fetchIDfromDB()
            except ValueError:
                self._createCategory()
        else:
            self._createCategory()

    def _fetchIDfromDB(self):
        search_query = "SELECT category.category_id, category.parent_id, category_description.name FROM `category`\
                        INNER JOIN `category_description` \
                        ON category.category_id = category_description.category_id \
                        WHERE category_description.name = '" + self.name + "'"
        if self.parent is not None:
            search_query += " AND category.parent_id = '" + self.parent.ID + "'"

        with self._connection.cursor() as cursor:
            cursor.execute(search_query)
            result = cursor.fetchall()
            if len(result) == 0:
                return None
            if len(result) == 1:
                return result[0]
            else:
                raise ValueError("Получили " + str(len(result)) + " совпадений по наименованию категории и ID \
                                родительской категории")


    def _createCategory(self):
        pass
