from collections import namedtuple
postprocess_pattern = namedtuple("PostProcessPattern", ["func", "attr", "check_value", "success_value"])

class Postprocessor:
    name = "postprocessor"

    def __init__(self, debug=False):
        self.rules = []
        self.debug = debug

    def add(self, rules):
        self.rules += rules

    def __call__(self, doc):
        # Iterate through the entities in reversed order
        for i in range(len(doc.ents)-1, -1, -1):
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
