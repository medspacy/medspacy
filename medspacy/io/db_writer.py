from .doc_consumer import (
    DEFAULT_DOC_ATTRS,
    DEFAULT_ENT_ATTRS,
    ALLOWED_CONTEXT_ATTRS,
    ALLOWED_SECTION_ATTRS,
)

DEFAULT_COLS = {
    "ent": list(DEFAULT_ENT_ATTRS),
    "doc": list(DEFAULT_DOC_ATTRS),
    "context": list(ALLOWED_CONTEXT_ATTRS),
    "section": list(ALLOWED_SECTION_ATTRS),
}

DEFAULT_COL_TYPES = {
    "ent": {
        "text": "varchar(50)",
        "start_char": "int",
        "end_char": "int",
        "label_": "varchar(50)",
        "is_negated": "int",
        "is_uncertain": "int",
        "is_historical": "int",
        "is_hypothetical": "int",
        "is_family": "int",
        "section_category": "int",
        "section_parent": "int",
    },
    "doc": {"text": "varchar(max)"},
    "section": {
        "section_category": "varchar(50)",
        "section_title_text": "varchar(50)",
        "section_title_start_char": "int",
        "section_title_end_char": "int",
        "section_text": "varchar(max)",
        "section_text_start_char": "int",
        "section_text_end_char": "int",
        "section_parent": "varchar(50)",
    },
    "context": {
        "ent_text": "varchar(50)",
        "ent_label_": "varchar(50)",
        "ent_start_char": "int",
        "ent_end_char": "int",
        "modifier_text": "varchar(50",
        "modifier_category": "varchar(50)",
        "modifier_direction": "varchar(50)",
        "modifier_start_char": "int",
        "modifier_end_char": "int",
        "modifier_scope_start_char": "int",
        "modifier_scope_end_char": "int",
    },
}


class DbWriter:
    """DbWriter is a utility class for writing structured data back to a database."""

    def __init__(
        self,
        db_conn,
        destination_table,
        cols=None,
        col_types=None,
        doc_dtype="ent",
        create_table=False,
        drop_existing=False,
        write_batch_size=100,
    ):
        """Create a new DbWriter object.

        Args:
            db_conn: A medspacy.io.DbConnect object
            destination_table: The name of the table to write to
            cols (opt): The names of the columns of the destination table. These should align with attributes extracted
                by DocConsumer and stored in doc._.data. A set of default values can be accessed by:
                >>> DbWriter.get_default_cols()
            col_types (opt): The sql data types of the table columns. They should correspond 1:1 with cols.
                A set of default values can be accesed by:
                >>> DbWriter.get_default_col_types()
            doc_dtype: The type of data from DocConsumer to write from a doc.
                Either ("ent", "section", "context", or "doc")
            create_table (bool): Whether to create a table

        """
        self.db = db_conn
        self.destination_table = destination_table
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

        self.insert_query = ""
        if create_table:
            self.create_table()
        self.make_insert_query()

    @classmethod
    def get_default_col_types(cls, dtypes=None):

        if dtypes is None:
            dtypes = tuple(DEFAULT_COL_TYPES.keys())
        else:
            if isinstance(dtypes, str):
                dtypes = (dtypes,)

        _validate_dtypes(dtypes)
        dtype_col_types = {
            dtype: col_types for (dtype, col_types) in DEFAULT_COL_TYPES.items() if dtype in dtypes
        }
        return dtype_col_types

    @classmethod
    def get_default_cols(cls, dtypes=None):
        if dtypes is None:
            dtypes = tuple(DEFAULT_COL_TYPES.keys())
        else:
            if isinstance(dtypes, str):
                dtypes = (dtypes,)
        _validate_dtypes(dtypes)

        dtype_cols = {dtype: cols for (dtype, cols) in DEFAULT_COL_TYPES.items() if dtype in dtypes}
        return dtype_cols

    def create_table(self):
        query = "CREATE TABLE {0} (".format(self.destination_table)
        for i, col in enumerate(self.cols):
            query += "{0} {1}".format(col, self.col_types[i])
            if i < len(self.cols) - 1:
                query += ", "
            else:
                query += ")"
        self.db.create_table(query, self.destination_table, self.drop_existing)

    def make_insert_query(self):
        col_list = ", ".join([col for col in self.cols])
        q_list = ", ".join(["?" for col in self.cols])
        self.insert_query = "INSERT INTO {0} ({1}) VALUES ({2})".format(
            self.destination_table, col_list, q_list
        )

    def write(self, doc):
        """Write a doc to a database."""
        data = doc._.get_data(self.doc_dtype, attrs=self.cols, as_rows=True)
        self.write_data(data)

    def write_data(self, data):
        self.db.write(self.insert_query, data)

    def close(self):
        self.db.close()


def _validate_dtypes(dtypes):
    for dtype in dtypes:
        if dtype not in DEFAULT_COL_TYPES:
            raise ValueError("Invalid doc dtype:", dtype)
