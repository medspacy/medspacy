import pandas as pd


class Pipeline:
    def __init__(self, reader, writer, nlp, dtype):
        self.reader = reader
        self.writer = writer
        self.nlp = nlp
        self.dtype = dtype

    def process(self):
        query_result = self.reader.read()
        data = None
        while query_result:
            if len(query_result) > 0:
                query_zip = list(zip(*query_result))
                ids = query_zip[0]
                texts = query_zip[1]

                docs = self.nlp.pipe(texts)

                for i, doc in enumerate(docs):
                    id = ids[i]
                    doc_data = pd.DataFrame(data=doc._.get_data(self.dtype, dtype=self.dtype))
                    doc_data.insert(0, self.writer.cols[0], [id for j in range(doc_data.shape[0])])

                    if data is None:
                        data = doc_data.copy()
                    else:
                        data = data.append(doc_data.copy())

                    if data.shape[0] >= self.writer.batch_size:
                        self.writer.write(data)
                        data = None
            query_result = self.reader.read()

        if data is not None:
            print("WRITING DOCS")
            self.writer.write(data)
            data = None

        self.reader.close()
        self.writer.close()
