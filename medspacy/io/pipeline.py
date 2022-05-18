from .doc_consumer import ALLOWED_DATA_TYPES
from spacy.language import Language


@Language.factory("medspacy_pipeline")
class Pipeline:
    """The Pipeline class executes a batch process of reading texts, processing them with a spaCy model, and writing
    the results back to a database.
    """

    def __init__(self, nlp, reader, writer, name="medspacy_pipeline", dtype="ent"):
        """Create a new Pipeline object.
        Args:
            reader: A DbReader object
            writer: A Dbwriter object
            nlp: A spaCy model
            dtype: The DocConsumer data type to write to a database.
                Default "ent
                Valid options are ("ent", "section", "context", "doc")
        """

        self.reader = reader
        self.writer = writer
        self.name = name
        self.nlp = nlp
        self.dtype = dtype
        if dtype not in ALLOWED_DATA_TYPES:
            raise ValueError(
                "Invalid dtypes. Supported dtypes are {0}, not {1}".format(
                    ALLOWED_DATA_TYPES, dtype
                )
            )

    def process(self):
        """Run a pipeline by reading a set of texts from a source table, processing them with nlp,
        and writing doc._.data back to the destination table.
        """
        query_result = self.reader.read()
        data = None
        while query_result:
            if len(query_result) > 0:
                query_zip = list(zip(*query_result))
                ids = query_zip[0]
                texts = query_zip[1]

                docs = self.nlp.pipe(texts)

                for i, doc in enumerate(docs):
                    text_id = ids[i]
                    # Get the data as rows of tuples
                    doc_data = doc._.get_data(self.dtype, as_rows=True)
                    # Add the identifier column
                    doc_data = [(text_id,) + row_data for row_data in doc_data]
                    # doc_data.insert(0, self.writer.cols[0], [text_id for _ in range(len(doc_data))])
                    # doc_data = pd.DataFrame(data=doc._.get_data(self.dtype))
                    # doc_data.insert(0, self.writer.cols[0], [text_id for _ in range(len(doc_data))])

                    if data is None:
                        data = doc_data.copy()
                    else:
                        data += doc_data.copy()
                    if len(data) >= self.writer.batch_size:
                        self.writer.write_data(data)
                        data = None
            query_result = self.reader.read()

        if data is not None:
            self.writer.write_data(data)
            data = None

        self.reader.close()
        if self.writer.db.conn != self.reader.db.conn:
            self.writer.close()
