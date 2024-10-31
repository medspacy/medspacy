# db_writer.py
from sqlalchemy import Column, Integer, String, Text, MetaData, Table
from sqlalchemy.orm import declarative_base

from typing import Union, List
from spacy.tokens import Doc

from .doc_consumer import (
    DEFAULT_DOC_ATTRS,
    DEFAULT_ENT_ATTRS,
    ALLOWED_CONTEXT_ATTRS,
    ALLOWED_SECTION_ATTRS,
)

DEFAULT_COLS = {
    "ents": list(DEFAULT_ENT_ATTRS),
    "doc": list(DEFAULT_DOC_ATTRS),
    "context": list(ALLOWED_CONTEXT_ATTRS),
    "section": list(ALLOWED_SECTION_ATTRS),
}

DEFAULT_COL_TYPES = {
    "ents": {
        "text": String(50),
        "start_char": Integer,
        "end_char": Integer,
        "label_": String(50),
        "is_negated": Integer,
        "is_uncertain": Integer,
        "is_historical": Integer,
        "is_hypothetical": Integer,
        "is_family": Integer,
        "section_category": String(50),
        "section_parent": String(50),
    },
    "doc": {"text": Text},
    "section": {
        "section_category": String(50),
        "section_title_text": String(50),
        "section_title_start_char": Integer,
        "section_title_end_char": Integer,
        "section_body": Text,
        "section_body_start_char": Integer,
        "section_body_end_char": Integer,
        "section_parent": String(50),
    },
    "context": {
        "ent_text": String(50),
        "ent_label_": String(50),
        "ent_start_char": Integer,
        "ent_end_char": Integer,
        "modifier_text": String(50),
        "modifier_category": String(50),
        "modifier_direction": String(50),
        "modifier_start_char": Integer,
        "modifier_end_char": Integer,
        "modifier_scope_start_char": Integer,
        "modifier_scope_end_char": Integer,
    },
}

Base = declarative_base()

class DbWriter:
    """DbWriter is a utility class for writing structured data back to a database using SQLAlchemy."""

    def __init__(
        self,
        db_conn,
        destination_table_name,
        cols=None,
        col_types=None,
        doc_dtype="ents",
        create_table=False,
        drop_existing=False,
        write_batch_size=100,
    ):
        self.db = db_conn
        self.destination_table_name = destination_table_name
        self._create_table = create_table
        self.drop_existing = drop_existing
        if cols is None and col_types is None:
            cols = DEFAULT_COLS[doc_dtype]
            col_types = [DEFAULT_COL_TYPES[doc_dtype][col] for col in cols]
        elif cols is None and col_types is not None:
            raise ValueError("cols must be specified if col_types is not None.")
        self.cols = cols
        self.col_types = col_types
        _validate_dtypes((doc_dtype,))
        self.doc_dtype = doc_dtype
        self.batch_size = write_batch_size

        if create_table:
            self.create_table()
        else:
            # If the table already exists, reflect it
            metadata = MetaData(bind=self.db.engine)
            self.table = Table(self.destination_table_name, metadata, autoload_with=self.db.engine)

    @classmethod
    def get_default_col_types(cls, dtypes=None):
        if dtypes is None:
            dtypes = tuple(DEFAULT_COL_TYPES.keys())
        else:
            if isinstance(dtypes, str):
                dtypes = (dtypes,)

        _validate_dtypes(dtypes)
        dtype_col_types = {
            dtype: col_types
            for (dtype, col_types) in DEFAULT_COL_TYPES.items()
            if dtype in dtypes
        }
        return dtype_col_types

    @classmethod
    def get_default_cols(cls, dtypes=None):
        if dtypes is None:
            dtypes = tuple(DEFAULT_COLS.keys())
        else:
            if isinstance(dtypes, str):
                dtypes = (dtypes,)
        _validate_dtypes(dtypes)
        dtype_cols = {
            dtype: cols
            for (dtype, cols) in DEFAULT_COLS.items()
            if dtype in dtypes
        }
        return dtype_cols

    def create_table(self):
        metadata = MetaData()
        columns = []
        for col_name, col_type in zip(self.cols, self.col_types):
            columns.append(Column(col_name, col_type))
        self.table = Table(
            self.destination_table_name,
            metadata,
            *columns,
        )
        if self.drop_existing:
            self.table.drop(self.db.engine, checkfirst=True)
        self.table.create(self.db.engine, checkfirst=True)
        print(f"Created table {self.table.name}")

    def reflect_table(self):
        metadata = MetaData()
        self.table = Table(
            self.destination_table_name,
            metadata,
            autoload_with=self.db.engine,
        )
        print(f"Reflected existing table {self.table.name}")

    def write(self, docs: Union[Doc, List[Doc]]):
        """Write a list of docs or a single doc to the database."""
        if isinstance(docs, Doc):
            self.write_doc(docs)
        else:
            self.write_docs(docs)

    def write_doc(self, doc):
        """Write a single doc to the database."""
        data = doc._.get_data(self.doc_dtype, attrs=self.cols, as_rows=True)
        self.write_data(data)

    def write_docs(self, docs, batch_size=None):
        """Write multiple docs to the database in batches."""
        if batch_size is None:
            batch_size = self.batch_size
        data = []
        for doc in docs:
            data.extend(doc._.get_data(self.doc_dtype, attrs=self.cols, as_rows=True))
            if len(data) >= batch_size:
                self.write_data(data)
                data = []
        if len(data) > 0:
            self.write_data(data)

    def write_data(self, data):
        # Convert data to list of dictionaries
        data_dicts = [dict(zip(self.cols, row)) for row in data]
        self.db.write(self.table, data_dicts)

    def close(self):
        self.db.close()

def _validate_dtypes(dtypes):
    for dtype in dtypes:
        if dtype not in DEFAULT_COLS:
            raise ValueError("Invalid doc dtype:", dtype)
