from . import TargetMatcher
from spacy.tokens import Token

class ConceptTagger:
    """ConceptTagger is a component for setting an attribute on tokens contained
    in spans extracted by TargetRules. This can be used for semantic labeling
    for normalizing tokens, making downstream extraction simpler.
    """

    name = "concept_tagger"

    def __init__(self, nlp, attr_name="concept_tag"):
        """Create a new ConceptTagger.
        Params:
            nlp: A spaCy Language model.
            attr_name (str): The name of the attribute to set to tokens.
        """
        self.nlp = nlp
        self.attr_name = attr_name
        self.target_matcher = TargetMatcher(nlp, add_ents=False)
        self.rules = []

        # If the token attribute hasn't been set, add it now
        try:
            Token.set_extension(attr_name, default="")
        except:
            pass

    def add(self, rules):
        self.target_matcher.add(rules)
        for rule in rules:
            self.rules.append(rule)

    def __call__(self, doc):
        spans = self.target_matcher(doc)
        for span in spans:
            for token in span:
                setattr(token._, self.attr_name, span.label_)

        return doc
