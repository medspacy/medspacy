import pytest

driver = ""
server = "test"
db = "test"
user = ""
pwd = ""


class TestDbConnect:
    @pytest.mark.skip(reason="not currently implemented with sqlite")
    def test_init_from_conn_info(self):
        from medspacy.io.db_connect import DbConnect
        db_conn = DbConnect(driver, server, db, user, pwd)
        assert db_conn is not None

    def test_init_from_sqlite3_conn(self):
        from medspacy.io.db_connect import DbConnect
        import sqlite3
        sq_conn = sqlite3.connect(db)
        db_conn = DbConnect(conn=sq_conn)
        assert db_conn is not None
        db_conn.close()
