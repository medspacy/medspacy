import os
import sys
import time

sys.path.append(os.getcwd())
import os
import tempfile

from medspacy.io.db_connect import DbConnect
import sqlite3

import medspacy
from medspacy.target_matcher import TargetRule
from medspacy.io import DocConsumer

def main():
    """
    benchmark db write_doc vs write_docs
    write_docs takes 2.1695 seconds.
    write doc takes 134.8181 seconds.
    """
    duplicates=200000
    tmpdirname = tempfile.TemporaryDirectory()
    db = os.path.join(tmpdirname.name, "test")

    nlp = medspacy.load(
        enable=["medspacy_pyrush", "medspacy_target_matcher", "medspacy_context", "medspacy_sectionizer"])
    nlp.get_pipe("medspacy_target_matcher").add(TargetRule("pneumonia", "CONDITION"))
    doc = nlp("There is no evidence of pneumonia.")

    doc_consumer = DocConsumer(nlp)
    doc_consumer(doc)
    sq_conn = sqlite3.connect(db)
    cursor = sq_conn.cursor()
    db_conn = DbConnect(conn=sq_conn)
    from medspacy.io.db_writer import DbWriter
    writer = DbWriter(db_conn, "ents", cols=None, col_types=None, create_table=True, drop_existing=False)
    start = time.time()
    writer.write([doc] * duplicates)
    print(f'write_docs takes {time.time() - start:.4f} seconds.')
    cursor.execute("DELETE FROM ents;")
    cursor.connection.commit()
    start = time.time()
    for i in range(duplicates):
        writer.write(doc)
    print(f'write doc takes {time.time() - start:.4f} seconds.')
    db_conn.close()
    from pathlib import Path
    Path(db).unlink()

main()