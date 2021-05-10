from PyRuSH import PyRuSHSentencizer
from spacy.language import Language

from os import path
from pathlib import Path

@Language.factory("pyrush")
def create_pyrush(nlp, name):
    pyrush_path = path.join(
        Path(__file__).resolve().parents[1], "resources", "rush_rules.tsv"
    )

    return PyRuSHSentencizer(pyrush_path)