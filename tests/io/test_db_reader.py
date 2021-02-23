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


def create_test_db(db, drop_existing=True):
    import os
    if drop_existing and os.path.exists(db):
        print("File medspacy_demo.db already exists")
        return

    import sqlite3 as s3

    texts = [
        "Patient with a history of breast ca",
        "There is no evidence of pneumonia."
    ]

    conn = s3.connect(db)

    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS texts;")
    cursor.execute("CREATE TABLE texts (text_id INTEGER PRIMARY KEY, text NOT NULL);")

    for text in texts:
        cursor.execute("INSERT INTO texts (text) VALUES (?)", (text,))

    conn.commit()
    conn.close()
    print("Created file", db)

class TestDbWriter:

    def test_init_from_sqlite3_conn(self):
        from medspacy.io.db_connect import DbConnect
        import sqlite3
        create_test_db(db)
        sq_conn = sqlite3.connect(db)

        db_conn = DbConnect(conn=sq_conn)
        from medspacy.io.db_reader import DbReader
        reader = DbReader(db_conn, "SELECT text_id, text FROM texts")
        rslts = reader.read()
        assert rslts[0] == (1, "Patient with a history of breast ca")
        assert rslts[1] == (2, "There is no evidence of pneumonia.")
        db_conn.close()
