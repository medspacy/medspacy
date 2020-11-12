import pyodbc


class DbReader:
    def __init__(self, db_conn, read_query, start=-1, end=-1, read_batch_size=-1):
        self.db = db_conn
        self.read_query = read_query
        self.start = start
        self.end = end
        self.batch_size = read_batch_size

    def read(self):
        if self.read_batch_size < 0:
            result = self.db.read(self.read_query)
        elif self.start >= self.end:
            result = None
        else:
            result = self.db.read(self.read_query.format(self.start, self.start + self.batch_size))
        return result

    def close(self):
        self.db.close()
