from medspacy.io import DbConnect

driver = "SQLite3 ODBC Driver"
server = "test"
db = "test"
user = ""
pwd = ""


class TestDbConnect:
    def test_init(self):
        db_conn = DbConnect(driver, server, db, user, pwd)
        assert db_conn is not None
