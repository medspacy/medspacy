from PyRuSH import PyRuSHSentencizer
import pysbd
from spacy.language import Language

from os import path
from pathlib import Path


# @Language.factory("medspacy_pyrush")
# def create_pyrush(nlp, name, pyrush_path=None):
#     if pyrush_path is None:
#         pyrush_path = path.join(
#             Path(__file__).resolve().parents[1], "resources", "rush_rules.tsv"
#         )
#     return PyRuSHSentencizer(pyrush_path)


@Language.factory("medspacy_pysbd")
class PySBDSenteceSplitter:
    def __init__(self, name, nlp, clean=False):
        self.name = name
        self.nlp = nlp
        self.seg = pysbd.Segmenter(language="en", clean=clean, char_span=True)

    def __call__(self, doc):
        """
        Spacy component based on: https://github.com/nipunsadvilkar/pySBD improved to work with spacy 3.0
        """
        sents_char_spans = self.seg.segment(doc.text_with_ws)
        start_token_ids = [sent.start for sent in sents_char_spans]
        for token in doc:
            token.is_sent_start = True if token.idx in start_token_ids else False
        return doc
