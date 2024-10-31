# db_connect.py
from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker

class DbConnect:
    """DbConnect is a wrapper for SQLAlchemy engine and session.
    It can then be passed into the DbReader and DbWriter classes
    to retrieve/store document data.
    """

    def __init__(
        self,
        connection_string=None,
        conn=None,
        echo=False,
        fast_executemany=False,  # Added parameter
    ):
        """Create a new DbConnect object.

        Args:
            connection_string (str): The database connection string.
                Example for SQLite: 'sqlite:///example.db'
                Example for PostgreSQL: 'postgresql://user:password@localhost/dbname'
            conn: An existing SQLAlchemy engine or connection.
            echo (bool): If True, the engine will log all statements.
            fast_executemany (bool): If True and using pyodbc with SQL Server,
                                     enables fast_executemany for bulk inserts.
        """
        if conn is None:
            if not connection_string:
                raise ValueError(
                    "If you are not passing in a connection object, "
                    "you must provide a valid connection string."
                )

            # Check if using pyodbc with SQL Server
            if 'mssql+pyodbc' in connection_string.lower():
                connect_args = {'fast_executemany': fast_executemany}
            else:
                connect_args = {}

            self.engine = create_engine(
                connection_string,
                echo=echo,
                connect_args=connect_args
            )
            self.conn = self.engine.connect()
        else:
            self.engine = conn.engine
            self.conn = conn

        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        self.database_exception = exc.SQLAlchemyError

        print(f"Opened connection to {self.engine.url}")

    def create_table(self, table, drop_existing=False):
        """Create a table using SQLAlchemy's metadata.

        Args:
            table: SQLAlchemy Table object.
            drop_existing (bool): Whether to drop the table if it exists.
        """
        if drop_existing:
            table.drop(self.engine, checkfirst=True)
        table.create(self.engine, checkfirst=True)
        print(f"Created table {table.name}")

    def write(self, table, data):
        """Write data to the database using session.

        Args:
            table: The SQLAlchemy Table object.
            data: A list of dictionaries matching the table's columns.
        """
        try:
            # Use the insert construct
            insert_stmt = table.insert()
            self.session.execute(insert_stmt, data)
            self.session.commit()
        except self.database_exception as e:
            self.session.rollback()
            raise e
        else:
            print(f"Wrote {len(data)} rows.")

    def read(self, query):
        """Execute a read query.

        Args:
            query: A SQLAlchemy query object.
        """
        result = self.session.execute(query).fetchall()
        print(f"Read {len(result)} rows.")
        return result

    def close(self):
        self.session.close()
        self.conn.close()
        print("Connection closed.")
