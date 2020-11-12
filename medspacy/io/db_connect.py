import pyodbc


class DbConnect:
    def __init__(self, driver, server, db, user, pwd):
        self.conn = pyodbc.connect("DRIVER={0};SERVER={1};DATABASE={2};USER={3};PWD={4}".format(driver, server, db, user, pwd))
        self.cursor = self.conn.cursor()
        print("Opened connection to {0}.{1}".format(server, db))

    def create_table(self, query, table_name, drop_existing):
        if drop_existing:
            try:
                self.cursor.execute("drop table {0}".format(table_name))
            except pyodbc.DatabaseError:
                print("Cannot drop {0}. Table does not exist.".format(table_name))
            else:
                self.conn.commit()
        try:
            self.cursor.execute(query)
        except pyodbc.DatabaseError as err:
            self.conn.rollback()
            self.conn.close()
            raise err
        else:
            self.conn.commit()

    def write(self, query, data):
        try:
            self.cursor.executemany(query, data)
        except pyodbc.DatabaseError as err:
            self.conn.rollback()
            self.conn.close()
            raise err
        else:
            self.conn.commit()

    def read(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        self.conn.commit()
        self.conn.close()
