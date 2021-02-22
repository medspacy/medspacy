class DbConnect:
    """DbConnect is a wrapper for either a pyodbc or sqlite3 connection. It can then be
    passed into the DbReader and DbWriter classes to retrieve/store document data.
    """
    def __init__(self, driver=None, server=None, db=None, user=None, pwd=None, conn=None):
        """Create a new DbConnect object. You can pass in either information for a pyodbc connection string
        or directly pass in a sqlite or pyodbc connection object.

        If conn is None, all other arguments must be supplied. If conn is passed in, all other arguments will be ignored.

        Args:
            driver
            server
            db:
            user
            pwd
            conn
        """
        if conn is None:
            if not all([driver, server, db, user, pwd]):
                raise ValueError("If you are not passing in a connection object, "
                                 "you must pass in all other arguments to create a DB connection.")
            import pyodbc
            self.conn = pyodbc.connect("DRIVER={0};SERVER={1};DATABASE={2};USER={3};PWD={4}".format(driver, server, db, user, pwd))
        else:
            self.conn = conn
        self.cursor = self.conn.cursor()
        import sqlite3
        if isinstance(self.conn, sqlite3.Connection):
            self.db_lib = "sqlite3"
            self.database_exception = sqlite3.DatabaseError
        else:
            import pyodbc
            if isinstance(self.conn, pyodbc.Connection):
                self.db_lib = "pyodbc"
                self.database_exception = pyodbc.DatabaseError
            else:
                raise ValueError("conn must be either a sqlite3 or pyodbc Connection object, not {0}".format(type(self.conn)))


        print("Opened connection to {0}.{1}".format(server, db))



    def create_table(self, query, table_name, drop_existing):
        if drop_existing:
            try:
                self.cursor.execute("drop table if exists {0}".format(table_name))
            # except pyodbc.DatabaseError:
            except self.database_exception as e:
                pass
            else:
                self.conn.commit()
        try:
            self.cursor.execute(query)
        except self.database_exception as e:
            self.conn.rollback()
            self.conn.close()
            raise e
        else:
            self.conn.commit()
            print("Created table {0} with query: {1}".format(table_name, query))

    def write(self, query, data):
        try:
            self.cursor.executemany(query, data)
        except self.database_exception as e:
            self.conn.rollback()
            self.conn.close()
            raise e
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
