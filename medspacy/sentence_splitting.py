from PyRuSH import PyRuSHSentencizer
from spacy.language import Language

@Language.factory("sentencizer")
def make_pyrush_sentencizer(nlp, name, rules_path):
    return PyRuSHSentencizer(rules_path)