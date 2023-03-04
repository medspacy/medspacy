import pytest
import os
import tempfile

import medspacy
from medspacy.target_matcher import TargetRule
from medspacy.io import DocConsumer


tmpdirname = tempfile.TemporaryDirectory()
db = os.path.join(tmpdirname.name, "test.db")

# Set up a simple pipeline which will allow us to write results
nlp = medspacy.load(
    enable=[
        "medspacy_pyrush",
        "medspacy_target_matcher",
        "medspacy_context",
        "medspacy_sectionizer",
    ]
)
nlp.get_pipe("medspacy_target_matcher").add(
    [TargetRule("pneumonia", "CONDITION"), TargetRule("breast ca", "CONDITION")]
)
doc = nlp("There is no evidence of pneumonia.")

doc_consumer = DocConsumer(
    nlp, dtype_attrs={"ents": ["text", "label_", "is_negated", "section_category"]}
)
nlp.add_pipe(
    "medspacy_doc_consumer",
    config={
        "dtype_attrs": {"ents": ["text", "label_", "is_negated", "section_category"]}
    },
)

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
        "There is no evidence of pneumonia.",
        "Patient with a history of breast ca",
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


class TestPipeline:
    def test_init_from_sqlite3_conn(self):
        from medspacy.io.db_connect import DbConnect
        import sqlite3

        create_test_db(db)
        sq_conn = sqlite3.connect(db)

        db_conn = DbConnect(conn=sq_conn)

        from medspacy.io.db_reader import DbReader

        reader = DbReader(db_conn, "SELECT text_id, text FROM texts")

        from medspacy.io.db_writer import DbWriter

        writer = DbWriter(
            db_conn,
            "ents",
            ["text_id"] + doc_consumer.dtype_attrs["ents"],
            ["int"] + db_dtypes,
            create_table=True,
            drop_existing=False,
        )

        from medspacy.io.pipeline import Pipeline

        pipeline = Pipeline(nlp, reader, writer, nlp, "ents")
        pipeline.process()

        sq_conn = sqlite3.connect(db)
        cursor = sq_conn.cursor()
        cursor.execute("SELECT * FROM ents;")
        rslts = cursor.fetchall()
        assert rslts[0] == (1, "pneumonia", "CONDITION", True, None)
        assert rslts[1] == (2, "breast ca", "CONDITION", False, None)
        sq_conn.close()
