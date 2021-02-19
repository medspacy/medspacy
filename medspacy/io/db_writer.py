class DbWriter:
    """DbWriter is a utility class for writing structured data back to a database.
    """
    def __init__(self, db_conn, destination_table, cols, col_types, doc_dtype="ent",
                 create_table=False, drop_existing=False,write_batch_size=100):
        """Create a new DbWriter object.

        Args:
            db_conn: A medspacy.io.DbConnect object
            destination_table: The name of the table to write to
            cols: The names of the columns of the destination table
            col_types: The sql data types of the table columns
            doc_dtype: The type of data from DocConsumer to write from a doc.
                Either ("ent", "section", "context", or "doc")
            create_table (bool): Whether to create a table

        """
        self.db = db_conn
        self.destination_table = destination_table
        self._create_table = create_table
        self.drop_existing = drop_existing
        self.cols = cols
        self.col_types = col_types
        self.doc_dtype = doc_dtype
        self.batch_size = write_batch_size

        self.insert_query = ""
        if create_table:
            self.create_table()
        self.make_insert_query()

    def create_table(self):
        query = "CREATE TABLE {0} (".format(self.destination_table)
        for i, col in enumerate(self.cols):
            query += "{0} {1}".format(col, self.col_types[i])
            if i < len(self.cols) - 1:
                query += ", "
            else:
                query += ")"
        self.db.create_table(query, self.destination_table, self.drop_existing)

    def make_insert_query(self):
        col_list = ", ".join([col for col in self.cols])
        q_list = ", ".join(["?" for col in self.cols])
        self.insert_query = "INSERT INTO {0} ({1}) VALUES ({2})".format(self.destination_table, col_list, q_list)

    def write(self, doc):
        """Write a doc to a database."""
        data = doc._.get_data(self.doc_dtype, as_rows=True)
        self.db.write(self.insert_query, data)

    def close(self):
        self.db.close()
