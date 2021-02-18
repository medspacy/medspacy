import pyodbc


class DbConnect:
    def __init__(self, driver=None, server=None, db=None, user=None, pwd=None, conn=None):
        if conn is None:
            if not all([driver, server, db, user, pwd]):
                raise ValueError("If you are not passing in a connection object, "
                                 "you must pass in all other arguments to create a DB connection.")
            self.conn = pyodbc.connect("DRIVER={0};SERVER={1};DATABASE={2};USER={3};PWD={4}".format(driver, server, db, user, pwd))
        else:
            self.conn = conn
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
            print("Created table {0} with query: {1}".format(table_name, query))

    def write(self, query, data):
        try:
            self.cursor.executemany(query, data)
        except pyodbc.DatabaseError as err:
            self.conn.rollback()
            self.conn.close()
            raise err
        else:
            self.conn.commit()
            print("Wrote {0} rows with query: {1}".format(len(data), query))

    def read(self, query):
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        print("Read {0} rows with query: {1}".format(len(result), query))
        return result

    def close(self):
        self.conn.commit()
        self.conn.close()
        print("Connection closed.")
