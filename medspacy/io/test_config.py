import spacy

from db_connect import DbConnect
from db_reader import DbReader
from db_writer import DbWriter
from doc_consumer import DocConsumer
from pipeline import Pipeline

# sql config
server = "test_server"
db = "test_db"
user = ""
pwd = ""

# destination settings
destination_table = "table_name"
create_table = True
drop_existing = True
write_batch_size = 25
row_type = "ents"  # 'ents' or 'sections'
# column specifier, not implemented
cols = ["id", "text_", "start_char", "end_char", "label", "label_"]
col_types = ["bigint", "varchar(50)", "int", "int", "varchar(50)"]

# read settings
read_query = "select docid, text from read_table where rowid between {0} and {1}"
start = 0
end = 100
read_batch_size = 10

# make an NLP pipeline with doc_consumer component
nlp = spacy.load("en_core_web_sm")
consumer = DocConsumer(nlp)
nlp.add_pipe(consumer)

# make db connection
db_conn = DbConnect(server, db, user, pwd)

# make db read/write
db_reader = DbReader(db_conn, read_query, start, end, read_batch_size)
db_writer = DbWriter(db_conn, destination_table, create_table, drop_existing, write_batch_size, cols, col_types)

# make final pipeline
pipeline = Pipeline(db_reader, db_writer, nlp, row_type)
