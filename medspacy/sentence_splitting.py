from PyRuSH import PyRuSHSentencizer
from spacy.language import Language

from os import path
from pathlib import Path

@Language.factory("medspacy_pyrush")
def create_pyrush(nlp, name, pyrush_path=None):
    if pyrush_path is None:
        pyrush_path = path.join(
            Path(__file__).resolve().parents[1], "resources", "rush_rules.tsv"
        )

    return PyRuSHSentencizer(pyrush_path)
