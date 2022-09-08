import spacy

from medspacy.io.db_connect import DbConnect
from medspacy.io.db_reader import DbReader
from medspacy.io.db_writer import DbWriter
from medspacy.io.doc_consumer import DocConsumer
from medspacy.io.pipeline import Pipeline

from medspacy.context import ConTextComponent
from medspacy.section_detection import Sectionizer

#####################################################
# SQL CONNECTION CONFIG
# Specify your sql connection
driver = "SQL Server"
server = "your_server"
db = "your_db"
user = ""
pwd = ""
#####################################################


#####################################################
# DATA DESTINATION CONFIG
# Specify where your output table is, how to interact
# iwith tables that already exist, and how many rows
# to write at a time.
destination_table = "your_new_table"
create_table = True
drop_existing = True
write_batch_size = 100
#####################################################


#####################################################
# DATA FORMAT CONFIG
# Specify the columns names and types in the output
# table. ID column should be at index 0.
#
# Note: This is not yet fully configurable. It is
# dependent on the configuration of the DocConsumer
# shown later.
row_type = "ent"  # 'ent' or 'section'
if row_type == "ent":
    # ENT OPTIONS:
    #   DEFAULT: text (str), start_char (str), end_char (str), label_ (str)
    #   CONTEXT: is_family (bool), is_negated (bool), is_uncertain (bool),
    #            is_hypothetical (bool), is_historical (bool)
    #   SECTION: section_title (str), section_parent (str)
    cols = [
        "id",
        "text",
        "start_char",
        "end_char",
        "label_",
        "is_hypothetical",
        "section_title",
    ]
    col_types = [
        "bigint",
        "varchar(100)",
        "int",
        "int",
        "varchar(50)",
        "bit",
        "varchar(10)",
    ]

elif row_type == "section":
    # SECTION OPTIONS: section_title (str), section_title_text (str),
    #                  section_title_start_char (int), section_title_end_char (int),
    #                  section_text (str), section_text_start_char (int),
    #                  section_text_end_char (int), section_parent (str)
    cols = [
        "id",
        "section_title",
        "section_title_text",
        "section_title_start_char",
        "section_title_end_char",
        "section_text",
        "section_text_start_char",
        "section_text_end_char",
        "section_parent",
    ]
    col_types = [
        "bigint",
        "varchar(200)",
        "varchar(max)",
        "int",
        "int",
        "varchar(max)",
        "int",
        "int",
        "varchar(200)",
    ]
#####################################################


#####################################################
# DATA READING CONFIGS
# Specify your data input configs. Query should be of
# format SELECT id, text FROM table. Batching info is
# OPTIONAL. If variables are not specified or if
# read_batch_size < 0, no batching will occur.
read_query = """select id, text
  from your_table
  where rowno>{0} and rowno<={1}"""
start = 0
end = 10
read_batch_size = 1
#####################################################


#####################################################
# NLP FACTORY
# initialize or call a method to produce your custom
# NLP pipeline here.
#
# NOTE: DocConsumer MUST be present at the end.
nlp = spacy.load("en_core_web_sm")
context = ConTextComponent(nlp)
sectionizer = Sectionizer(nlp, patterns=None)
sectionizer.add([{"section_title": "equals", "pattern": [{"LOWER": "=", "OP": "+"}]}])
consumer = DocConsumer(
    nlp, context=True, sectionizer=True
)  # DocConsumer has optional bool context and sectionizer
nlp.add_pipe(sectionizer)
nlp.add_pipe(context)
nlp.add_pipe(consumer)
#####################################################


#####################################################
# CREATING DB CONNECTIONS
db_read_conn = DbConnect(driver, server, db, user, pwd)
db_write_conn = DbConnect(driver, server, db, user, pwd)
#####################################################


#####################################################
# CREATING DB READ/WRITERS
db_reader = DbReader(
    db_read_conn, read_query, start, end, read_batch_size
)  # start, end, read_batch_size optional
db_writer = DbWriter(
    db_write_conn,
    destination_table,
    create_table,
    drop_existing,
    write_batch_size,
    cols,
    col_types,
)
#####################################################


#####################################################
# CREATING PIPELINE
pipeline = Pipeline(db_reader, db_writer, nlp, row_type)
#####################################################


#####################################################
# RUNNING NLP PIPELINE
pipeline.process()
#####################################################
