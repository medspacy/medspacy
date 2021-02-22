class DbReader:
    def __init__(self, db_conn, read_query, start=-1, end=-1, read_batch_size=-1):
        self.db = db_conn
        self.read_query = read_query
        self.start = start
        self.end = end
        self.batch_size = read_batch_size
        self.read_complete = False

    def read(self):
        if not self.read_complete:
            if self.batch_size < 0:
                result = self.db.read(self.read_query)
                self.read_complete = True
            else:
                result = self.db.read(self.read_query.format(self.start, self.start + self.batch_size))
                self.start += self.batch_size
                if self.start >= self.end:
                    self.read_complete = True
            return result
        else:
            return None

    def close(self):
        self.db.close()
