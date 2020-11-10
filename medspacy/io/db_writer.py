import pyodbc
import pandas as pd


class DbWriter:
    def __init__(self, db_conn, destination_table, create_table, drop_existing, write_batch_size, cols, col_types):
        self.db = db_conn
        self.destination_table = destination_table
        self.create_table = drop_existing
        self.cols = cols
        self.col_types = col_types
        self.batch_size = write_batch_size

        self.insert_query = ""
        if create_table:
            self.create_table()
        self.make_insert_query()

    def create_table(self):
        query = "CREATE TABLE {0} (".format(self.destination_table)
        for i, col in enumerate(self.cols):
            query += "{0} {1}".format(col, self.col_types[i])
            if i < len(self.cols - 1):
                query += ", "
            else:
                query += ")"
        self.db.create_table(query, self.destination_table, self.drop_existing)

    def make_insert_query(self):
        col_list = ", ".join([col for col in self.cols])
        q_list = ", ".join(["?" for col in self.cols])
        self.insert_query = "INSERT INTO {0} ({1}) VALUES ({2})".format(self.destination_table, col_list, q_list)

    def write(self, data):
        self.db.write(self.insert_query, data[self.cols].values.tolist())
