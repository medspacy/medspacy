import pytest
import os
import tempfile

import medspacy
from medspacy.target_matcher import TargetRule
from medspacy.io import DocConsumer

tmpdirname = tempfile.TemporaryDirectory()
db = os.path.join(tmpdirname.name, "test")

nlp = medspacy.load(enable=["sentencizer", "target_matcher", "context", "sectionizer"])
nlp.get_pipe("target_matcher").add(TargetRule("pneumonia", "CONDITION"))
doc = nlp("There is no evidence of pneumonia.")

doc_consumer = DocConsumer(nlp, dtype_attrs={"ent": ["text", "label_", "is_negated", "section_category"]})
doc_consumer(doc)

db_dtypes = [
    "varchar(100)",
    "varchar(100)",
    "int",
    "varchar(100)",
]

class TestDbWriter:

    def test_init_from_sqlite3_conn(self):
        from medspacy.io.db_connect import DbConnect
        import sqlite3
        sq_conn = sqlite3.connect(db)
        cursor = sq_conn.cursor()
        db_conn = DbConnect(conn=sq_conn)
        from medspacy.io.db_writer import DbWriter
        writer = DbWriter(db_conn, "ents", doc_consumer.dtype_attrs["ent"], db_dtypes,
                          create_table=True, drop_existing=False)
        writer.write(doc)
        cursor.execute("SELECT * FROM ents;")
        rslts = cursor.fetchone()
        assert rslts == ("pneumonia", "CONDITION", True, None)
        db_conn.close()
