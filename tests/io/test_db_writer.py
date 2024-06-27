import os, sys
from datetime import time, datetime

# recent pytest failed because of project directory is not included in sys.path somehow, might due to other configuration issue. Add this for a temp solution
sys.path.append(os.getcwd())
import pytest
import os
import tempfile

from medspacy.io.db_connect import DbConnect
import sqlite3

import medspacy
from medspacy.target_matcher import TargetRule
from medspacy.io import DocConsumer

tmpdirname = tempfile.TemporaryDirectory()
db = os.path.join(tmpdirname.name, "test")

nlp = medspacy.load(enable=["medspacy_pyrush", "medspacy_target_matcher", "medspacy_context", "medspacy_sectionizer"])
nlp.get_pipe("medspacy_target_matcher").add(TargetRule("pneumonia", "CONDITION"))
doc = nlp("There is no evidence of pneumonia.")

doc_consumer = DocConsumer(nlp)
doc_consumer(doc)


class TestDbWriter:
    def test_init_from_sqlite3_conn_defaults(self):
        """Test writing with default values for ent attributes."""
        sq_conn = sqlite3.connect(db)
        cursor = sq_conn.cursor()
        db_conn = DbConnect(conn=sq_conn)
        from medspacy.io.db_writer import DbWriter

        writer = DbWriter(db_conn, "ents", cols=None, col_types=None, create_table=True, drop_existing=False)
        writer.write(doc)
        cursor.execute("SELECT * FROM ents;")
        rslts = cursor.fetchone()
        assert rslts == ("pneumonia", 24, 33, "CONDITION", 1, 0, 0, 0, 0, None, None)
        db_conn.close()

    def test_init_write_docs(self):
        """Test writing with default values for ent attributes."""
        sq_conn = sqlite3.connect(db)
        cursor = sq_conn.cursor()
        db_conn = DbConnect(conn=sq_conn)
        from medspacy.io.db_writer import DbWriter

        writer = DbWriter(db_conn, "ents", cols=None, col_types=None, create_table=True, drop_existing=False)
        writer.write_docs([doc]*100)
        cursor.execute("SELECT COUNT(*) FROM ents;")
        rslts = cursor.fetchone()
        assert rslts[0] == 100
        db_conn.close()







    def test_init_from_sqlite3_conn_specific_cols(self):
        from medspacy.io.db_connect import DbConnect
        import sqlite3

        sq_conn = sqlite3.connect(db)
        cursor = sq_conn.cursor()
        db_conn = DbConnect(conn=sq_conn)

        cols = ["label_", "text", "is_negated", "section_category"]

        db_dtypes = [
            "varchar(100)",
            "varchar(100)",
            "int",
            "varchar(100)",
        ]

        from medspacy.io.db_writer import DbWriter

        writer = DbWriter(db_conn, "ents", cols=cols, col_types=db_dtypes, create_table=True, drop_existing=True)
        writer.write(doc)
        cursor.execute("SELECT * FROM ents;")
        rslts = cursor.fetchone()
        assert rslts == ("CONDITION", "pneumonia", True, None)
        db_conn.close()
