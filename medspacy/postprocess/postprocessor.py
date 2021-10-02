from collections import namedtuple
from spacy.language import Language

postprocess_pattern = namedtuple("PostProcessPattern", ["func", "attr", "check_value", "success_value"])


@Language.factory("medspacy_postprocessor")
class Postprocessor:
    def __init__(self, nlp, name="medspacy_postprocessor", debug=False):
        self.nlp = nlp
        self.name = name
        self.rules = []
        self.debug = debug

    def add(self, rules):
        self.rules += rules

    def __call__(self, doc):
        # Iterate through the entities in reversed order
        for i in range(len(doc.ents) - 1, -1, -1):
            ent = doc.ents[i]
            if self.debug:
                print(ent)
            for rule in self.rules:
                num_ents = len(doc.ents)
                rule(ent, i, self.debug)
                # Check if the entity was removed -if it was, skip to the next entity
                try:
                    if doc.ents[i] != ent:
                        break
                except IndexError:
                    break
            if self.debug:
                print()
        return doc
